"""
Memory Parser.

Converts natural-language memory requests into structured
memory operations.

This module does NOT:
- Write JSON files.
- Call MemoryService.
- Call the LLM.
- Modify projects, deadlines, or tasks.

It only identifies the requested memory operation and extracts
information that can be determined reliably.
"""

from __future__ import annotations

import re
import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryRequest:
    """Structured representation of a memory operation."""

    action: str

    # Project information
    name: Optional[str] = None
    description: str = ""

    # Deadline information
    title: Optional[str] = None
    date: Optional[str] = None
    excluded_title: Optional[str] = None

    # Task information
    due_date: Optional[str] = None

    # Relationship
    project_name: Optional[str] = None


class MemoryParser:
    # =========================================================
    # Public API
    # =========================================================

    def parse(self, prompt: str, history: list[dict] = None) -> Optional[MemoryRequest]:
        """
        Parse a user prompt into a MemoryRequest.

        READ operations are checked before WRITE operations so that
        questions such as "What deadlines do I have?" can never be
        mistaken for a request to create a deadline.
        """

        if not prompt or not prompt.strip():
            return None

        prompt = prompt.strip()

        # -----------------------------------------------------
        # Contextual Follow-up
        # -----------------------------------------------------
        if history:
            followup = self._parse_followup(prompt, history)
            if followup:
                return followup

        # -----------------------------------------------------
        # READ operations MUST be checked first.
        # -----------------------------------------------------
        read_request = self._parse_read(prompt)
        if read_request:
            return read_request

        # -----------------------------------------------------
        # WRITE operations
        # -----------------------------------------------------

        # Deadline removal MUST be checked before normal deadline creation
        removed_deadline = self._parse_remove_deadline(prompt)
        if removed_deadline:
            return removed_deadline

        # Deadline completion MUST be checked before normal
        # deadline creation.
        completed_deadline = self._parse_complete_deadline(prompt)
        if completed_deadline:
            return completed_deadline

        # A deadline can contain words like "project", so check
        # deadlines before generic project creation.
        deadline = self._parse_deadline(prompt)
        if deadline:
            return deadline

        task = self._parse_task(prompt)
        if task:
            return task

        project = self._parse_project(prompt)
        if project:
            return project

        return None

    # =========================================================
    # Contextual Follow-up
    # =========================================================

    def _parse_followup(self, prompt: str, history: list[dict]) -> Optional[MemoryRequest]:
        if not history or len(history) < 2:
            return None

        last_assistant = None
        last_user = None

        for i in range(len(history)-1, -1, -1):
            if history[i].get("role") == "assistant":
                last_assistant = history[i].get("content", "")
                if i - 1 >= 0 and history[i-1].get("role") == "user":
                    last_user = history[i-1].get("content", "")
                break

        if not last_assistant or not last_user:
            return None

        # Re-parse the last user prompt to see what it was
        prev_request = self.parse(last_user)

        if prev_request and prev_request.action == "add_deadline" and not prev_request.date:
            date = self._extract_date(prompt)
            if date:
                prev_request.date = date
                return prev_request

        return None

    # =========================================================
    # READ / QUERY
    # =========================================================

    def _parse_read(self, prompt: str) -> Optional[MemoryRequest]:
        """
        Detect queries asking Nexus to retrieve stored memory.

        Examples:
            "What deadlines do I have?"
            "Show my projects"
            "What tasks do I have?"
            "What do you remember about my work?"
        """

        lower = prompt.lower().strip()

        # Combined memory queries
        combined_patterns = (
            r"\bwhat do you remember\b",
            r"\bwhat do you know about my\b",
            r"\bshow my current memory\b",
            r"\bshow all my memory\b",
            r"\bwhat(?:'s| is) in my memory\b",
            r"\bwhat have you remembered\b",
        )

        if any(re.search(pattern, lower) for pattern in combined_patterns):
            return MemoryRequest(action="get_memory_summary")

        read_verbs = r"(?:what|show|list|lsit|display|get|fetch|retrieve|pull|tell me about|give me)"
        modifiers = r"(?:\s+me)?(?:\s+all)?(?:\s+the)?(?:\s+my)?"
        
        # Helper to check if "all" is explicitly in the prompt
        has_all = bool(re.search(r"\ball\b", lower))

        # Deadline queries
        deadline_patterns = (
            rf"\b{read_verbs}{modifiers}\s+deadlines?\b",
            r"\bwhat(?:'s| is) my next deadline\b",
            r"\bwhat deadlines? (?:are|is) coming\b",
            r"\bupcoming deadlines?\b",
        )
        if any(re.search(pattern, lower) for pattern in deadline_patterns):
            return MemoryRequest(action="get_all_deadlines" if has_all else "get_deadlines")

        # Project queries
        project_patterns = (
            rf"\b{read_verbs}{modifiers}\s+projects?\b",
            r"\bwhat projects? am i working on\b",
        )
        if any(re.search(pattern, lower) for pattern in project_patterns):
            return MemoryRequest(action="get_all_projects" if has_all else "get_projects")

        # Task queries
        task_patterns = (
            rf"\b{read_verbs}{modifiers}\s+tasks?\b",
            r"\bwhat do i need to do\b",
            r"\bwhat should i work on\b",
            r"\bwhat do i have to do\b",
        )
        if any(re.search(pattern, lower) for pattern in task_patterns):
            return MemoryRequest(action="get_all_tasks" if has_all else "get_tasks")

        return None

    # =========================================================
    # Intent Detection
    # =========================================================

    def _looks_like_memory_request(self, prompt: str) -> bool:
        """Determine whether the user appears to be storing information."""

        lower = prompt.lower()

        memory_keywords = (
            "remember",
            "keep in mind",
            "keep track",
            "save this",
            "store this",
            "don't forget",
            "do not forget",
            "deadline",
            "task",
            "project",
        )

        return any(keyword in lower for keyword in memory_keywords)

    def _looks_like_explicit_write(self, prompt: str) -> bool:
        """
        Require evidence that the user wants to STORE information.

        This prevents ordinary questions containing words like
        "deadline", "task", or "project" from becoming write operations.
        """

        lower = prompt.lower()

        write_patterns = (
            r"\bremember\b",
            r"\bsave\b",
            r"\bstore\b",
            r"\bkeep in mind\b",
            r"\bkeep track\b",
            r"\bdon'?t forget\b",
            r"\bdo not forget\b",
            r"\badd\b",
            r"\bcreate\b",
            r"\bmake\b",
            r"\bset\b",
            r"\bwrite\b",
            r"\bnote\b",
            r"\brecord\b",
            r"\bupdate\b",
            r"\bchange\b",
            r"\bmodify\b",
            r"\bi have\b",
            r"\bi've got\b",
            r"\bi need to\b",
            r"\bi have to\b",
            r"\bi should\b",
            r"\bi(?:'m| am) working on\b",
            r"\bi(?:'ve| have) started\b",
            r"\bi just started\b",
        )

        return any(re.search(pattern, lower) for pattern in write_patterns)

    # =========================================================
    # Project
    # =========================================================

    def _parse_project(self, prompt: str) -> Optional[MemoryRequest]:
        lower = prompt.lower()

        if not self._looks_like_explicit_write(prompt):
            return None

        project_patterns = [
            r"(?:remember|save|store)\s+(?:that\s+)?(?:i(?:'m| am)\s+)?(?:am\s+)?working\s+on\s+(?:a\s+)?(?:new\s+)?project\s+(?:called\s+)?(.+)",
            r"(?:remember|save|store)\s+(?:that\s+)?(?:my\s+)?project\s+(?:is\s+)?(?:called\s+)?(.+)",
            r"(?:i\s+)?(?:just\s+)?started\s+(?:working\s+on\s+)?(?:a\s+)?project\s+(?:called\s+)?(.+)",
        ]

        for pattern in project_patterns:
            match = re.search(pattern, lower, re.IGNORECASE)
            if not match:
                continue

            name = self._clean_name(match.group(1))
            if not name:
                return None

            return MemoryRequest(
                action="create_project",
                name=name,
            )

        return None

    # =========================================================
    # Deadline
    # =========================================================
    def _parse_remove_deadline(self, prompt: str) -> Optional[MemoryRequest]:
        lower = prompt.lower().strip()
        
        remove_patterns = (
            r"\bremove\b",
            r"\bdelete\b",
            r"\bclear\b",
            r"\berase\b",
        )
        
        has_remove_intent = any(
            re.search(pattern, lower)
            for pattern in remove_patterns
        )
        
        if not has_remove_intent or "deadline" not in lower:
            return None
            
        excluded_title = None
        except_match = re.search(r"\bexcept\s+(?:for\s+)?(?:the\s+)?(.+)", lower)
        if except_match:
            extracted = except_match.group(1).strip()
            extracted = re.sub(r"\s+deadline.*$", "", extracted).strip()
            if extracted and extracted not in {"this", "that", "my", "the"}:
                excluded_title = self._clean_name(extracted)
                
        if re.search(r"\b(?:all|remaining|every|everything)\b", lower):
            return MemoryRequest(action="remove_all_deadlines", excluded_title=excluded_title)
            
        title = None
        
        patterns = (
            r"(?:remove|delete|clear|erase)\s+(?:the\s+)?(.+?)\s+deadline\b",
            r"(?:remove|delete|clear|erase)\s+deadline\s+(?:for\s+|called\s+)?(.+?)\b",
        )
        
        for pattern in patterns:
            match = re.search(pattern, lower, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                if extracted and extracted not in {"this", "that", "my", "the"}:
                    title = self._clean_name(extracted)
                    break
                    
        return MemoryRequest(
            action="remove_deadline",
            title=title,
            date=self._extract_date(prompt)
        )

    def _parse_complete_deadline(
        self,
        prompt: str
    ) -> Optional[MemoryRequest]:
        """
        Detect requests to mark an existing deadline as completed.

        Examples:
            "I completed this deadline"
            "I finished my Physics deadline"
            "mark this deadline as completed"
            "mark the Physics deadline complete"
            "I have completed the Physics deadline"

        This must run before _parse_deadline() because completion
        requests also contain the word "deadline".
        """

        lower = prompt.lower().strip()

        # The prompt must clearly indicate completion.
        completion_patterns = (
            r"\bcompleted\b",
            r"\bcomplete\b",
            r"\bfinished\b",
            r"\bfinish\b",
            r"\bdone\b",
            r"\bmark\b.*\bcomplete\b",
            r"\bmark\b.*\bcompleted\b",
        )

        has_completion_intent = any(
            re.search(pattern, lower)
            for pattern in completion_patterns
        )

        if not has_completion_intent:
            return None

        # We only want this to operate on deadlines.
        if "deadline" not in lower:
            return None

        if re.search(r"\b(?:all|remaining|every|everything)\b", lower):
            return MemoryRequest(action="complete_all_deadlines")

        # -----------------------------------------------------
        # Try to extract a specific deadline title.
        # -----------------------------------------------------

        title = None

        patterns = (
            # "completed the Physics deadline"
            r"(?:completed|finished|finish|complete)"
            r"\s+(?:the\s+)?(.+?)\s+deadline\b",

            # "mark the Physics deadline complete"
            r"mark\s+(?:the\s+)?(.+?)\s+deadline"
            r"\s+(?:as\s+)?(?:complete|completed)\b",

            # "I have completed my Physics deadline"
            r"(?:i\s+have|i've)\s+(?:completed|finished)"
            r"\s+(?:my\s+|the\s+)?(.+?)\s+deadline\b",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                lower,
                re.IGNORECASE,
            )

            if match:
                extracted = match.group(1).strip()

                # Avoid returning generic words as the title.
                if extracted and extracted not in {
                    "this",
                    "that",
                    "my",
                    "the",
                }:
                    title = self._clean_name(extracted)
                    break

        # -----------------------------------------------------
        # Extract date if the user mentioned one.
        # -----------------------------------------------------

        date = self._extract_date(prompt)

        # -----------------------------------------------------
        # If we have neither a title nor a date, this is still
        # a valid completion request.
        #
        # The router can resolve it if there is only one
        # incomplete deadline.
        # -----------------------------------------------------

        print(
            "[Parser] Detected complete_deadline:",
            "title =", title,
            "date =", date,
        )

        return MemoryRequest(
            action="complete_deadline",
            title=title,
            date=date,
        )
    def _parse_deadline(self, prompt: str) -> Optional[MemoryRequest]:
        lower = prompt.lower()

        if "deadline" not in lower:
            return None

        if not self._looks_like_explicit_write(prompt):
            return None

        date = self._extract_date(prompt)
        title = self._extract_deadline_title(prompt)
        project_name = self._extract_project_name(prompt)
        description = prompt.strip()

        if not date:
            return MemoryRequest(
                action="add_deadline",
                title=title,
                description=description,
            )

        return MemoryRequest(
            action="add_deadline",
            title=title,
            date=date,
            project_name=project_name,
            description=description,
        )

    # =========================================================
    # Task
    # =========================================================

    def _parse_task(self, prompt: str) -> Optional[MemoryRequest]:
        lower = prompt.lower()

        task_keywords = (
            "task",
            "todo",
            "to-do",
            "need to",
            "have to",
            "should do",
        )

        if not any(keyword in lower for keyword in task_keywords):
            return None

        # Do not turn an ordinary question into a stored task.
        if not self._looks_like_explicit_write(prompt):
            return None

        title = None

        patterns = [
            r"(?:remember\s+)?(?:the\s+)?task\s+(?:is\s+)?(.+)",
            r"(?:remember\s+)?(?:i\s+)?need\s+to\s+(.+)",
            r"(?:remember\s+)?(?:i\s+)?have\s+to\s+(.+)",
            r"(?:remember\s+)?(?:i\s+)?should\s+(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, lower, re.IGNORECASE)

            if match:
                title = match.group(1).strip()
                break

        if not title:
            return None

        due_date = self._extract_date(prompt)
        project_name = self._extract_project_name(prompt)

        return MemoryRequest(
            action="add_task",
            title=self._clean_name(title),
            due_date=due_date,
            project_name=project_name,
        )

    # =========================================================
    # Date Extraction
    # =========================================================

    def _extract_date(self, prompt: str) -> Optional[str]:
        current_year = datetime.datetime.now().year

        print("[Parser for memory is running]")
        
        # YYYY-MM-DD or YYYY/MM/DD
        match = re.search(
            r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b",
            prompt,
        )
        if match:
            year, month, day = match.groups()
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"

        # MM/DD/YYYY, DD/MM/YYYY, MM-DD-YYYY, DD-MM-YYYY
        # We try to be smart: if the first number > 12, it must be DD.
        # Otherwise, assume MM/DD/YYYY (American style) by default, or you can assume DD/MM/YYYY.
        # Let's try to match both and use the one that is valid.
        match = re.search(
            r"\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b",
            prompt,
        )
        if match:
            part1, part2, year = match.groups()
            p1, p2 = int(part1), int(part2)
            
            # If part1 > 12, it has to be the day (DD/MM/YYYY)
            if p1 > 12:
                day, month = p1, p2
            # If part2 > 12, it has to be the day (MM/DD/YYYY)
            elif p2 > 12:
                month, day = p1, p2
            else:
                # Ambiguous (e.g. 10/11/2026). Let's default to MM/DD/YYYY (US format)
                month, day = p1, p2
                
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"

        # Today / Tomorrow
        lower = prompt.lower()
        if re.search(r"\btomorrow\b", lower):
            tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d")
        if re.search(r"\btoday\b", lower):
            today = datetime.datetime.now()
            return today.strftime("%Y-%m-%d")

        months = {
            "january": 1, "jan": 1,
            "february": 2, "feb": 2,
            "march": 3, "mar": 3,
            "april": 4, "apr": 4,
            "may": 5,
            "june": 6, "jun": 6,
            "july": 7, "jul": 7,
            "august": 8, "aug": 8,
            "september": 9, "sep": 9, "sept": 9,
            "october": 10, "oct": 10,
            "november": 11, "nov": 11,
            "december": 12, "dec": 12,
        }
        month_pattern = "|".join(months.keys())

        # DD Month YYYY (or without YYYY)
        match = re.search(
            rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?"
            rf"({month_pattern})"
            rf"(?:,?\s+(20\d{{2}}))?\b",
            prompt.lower(),
        )
        if match:
            day = int(match.group(1))
            month = months[match.group(2)]
            year = match.group(3)
            if not year:
                year = current_year
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"

        # Month DD YYYY (or without YYYY)
        match = re.search(
            rf"\b({month_pattern})\s+"
            rf"(\d{{1,2}})(?:st|nd|rd|th)?"
            rf"(?:,?\s+(20\d{{2}}))?\b",
            prompt.lower(),
        )
        if match:
            month = months[match.group(1)]
            day = int(match.group(2))
            year = match.group(3)
            if not year:
                year = current_year
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"

        return None

    # =========================================================
    # Project Name Extraction
    # =========================================================

    def _extract_project_name(self, prompt: str) -> Optional[str]:
        patterns = [
            r"(?:for|on|of)\s+(?:the\s+)?"
            r"([A-Za-z0-9][A-Za-z0-9 _-]{1,50}?)"
            r"\s+project\b",

            r"(?:project)\s+"
            r"([A-Za-z0-9][A-Za-z0-9 _-]{1,50}?)"
            r"(?:\s+deadline|\s+task|\s+due|\s+on\b|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)

            if match:
                return self._clean_name(match.group(1))

        return None

    # =========================================================
    # Deadline Title
    # =========================================================

    def _extract_deadline_title(self, prompt: str) -> str:
        lower = prompt.lower()
        
        patterns = [
            r"deadline\s+(?:for|to|of)\s+(?:a|an|the|my|our\s+)?(.+?)(?:\s+is\s+on\s+|\s+on\s+|\s+by\s+|\s+due\s+|$)",
            r"(?:have|got|set)\s+(?:a|an|the|my|our)?\s*(.+?)\s+deadline",
            r"(?:a|an|the|my|our)\s+(.+?)\s+deadline"
        ]
        
        for p in patterns:
            m = re.search(p, lower)
            if m:
                extracted = m.group(1).strip()
                if extracted and len(extracted) > 1 and "remember" not in extracted:
                    return self._clean_name(extracted)
                    
        project_name = self._extract_project_name(prompt)
        if project_name:
            return f"{project_name} deadline"

        return "Deadline"

    # =========================================================
    # Cleanup
    # =========================================================

    @staticmethod
    def _clean_name(value: str) -> str:
        value = value.strip()

        value = re.sub(
            r"[.!?,]+$",
            "",
            value,
        )

        return value.strip()
