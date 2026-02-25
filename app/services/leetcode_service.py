"""
LeetCode Service.

Fetches problem details from LeetCode's public GraphQL API.
Used by the DSA mode to get problem descriptions for teaching.
"""
import logging
import re
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql/"

# Query to get problem list and find slug by question number
PROBLEM_LIST_QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
    problemsetQuestionList: questionList(
        categorySlug: $categorySlug
        limit: $limit
        skip: $skip
        filters: $filters
    ) {
        total: totalNum
        questions: data {
            frontendQuestionId: questionFrontendId
            titleSlug
            title
            difficulty
        }
    }
}
"""

# Query to get full problem details by slug
PROBLEM_DETAIL_QUERY = """
query questionData($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        title
        titleSlug
        content
        difficulty
        topicTags {
            name
            slug
        }
        hints
        exampleTestcaseList
        sampleTestCase
    }
}
"""


def _strip_html(html: str) -> str:
    """Convert HTML content to plain text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    # Decode common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class LeetCodeService:
    """Service for fetching LeetCode problem data."""
    
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
        }
    
    async def get_problem_by_number(self, question_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a LeetCode problem by its question number.
        
        First finds the title slug, then fetches full details.
        
        Args:
            question_number: The LeetCode question number (e.g., 1 for Two Sum)
            
        Returns:
            Problem details dict or None if not found
        """
        try:
            # Search for the problem by number
            slug = await self._find_slug_by_number(question_number)
            if not slug:
                logger.warning(f"Could not find LeetCode problem #{question_number}")
                return None
            
            return await self.get_problem_by_slug(slug)
            
        except Exception as e:
            logger.error(f"Error fetching LeetCode problem #{question_number}: {e}")
            return None
    
    async def _find_slug_by_number(self, question_number: int) -> Optional[str]:
        """Find a problem's title slug by its frontend question number."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    LEETCODE_GRAPHQL_URL,
                    json={
                        "query": PROBLEM_LIST_QUERY,
                        "variables": {
                            "categorySlug": "all-code-essentials",
                            "skip": 0,
                            "limit": 1,
                            "filters": {
                                "searchKeywords": str(question_number),
                            },
                        },
                    },
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                
                questions = (
                    data.get("data", {})
                    .get("problemsetQuestionList", {})
                    .get("questions", [])
                )
                
                # Find exact match by frontend question ID
                for q in questions:
                    if str(q.get("frontendQuestionId")) == str(question_number):
                        return q["titleSlug"]
                
                # If search didn't work, try a broader search
                if not questions:
                    return None
                    
                return None
                
        except Exception as e:
            logger.error(f"Error searching for problem #{question_number}: {e}")
            return None
    
    async def get_problem_by_slug(self, title_slug: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full problem details by title slug.
        
        Args:
            title_slug: The problem's URL slug (e.g., "two-sum")
            
        Returns:
            Problem details dict
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    LEETCODE_GRAPHQL_URL,
                    json={
                        "query": PROBLEM_DETAIL_QUERY,
                        "variables": {"titleSlug": title_slug},
                    },
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                
                question = data.get("data", {}).get("question")
                if not question:
                    return None
                
                # Parse and structure the response
                content_html = question.get("content", "")
                description = _strip_html(content_html) if content_html else ""
                
                return {
                    "number": question.get("questionFrontendId"),
                    "title": question.get("title", ""),
                    "slug": question.get("titleSlug", ""),
                    "difficulty": question.get("difficulty", "Unknown"),
                    "description": description,
                    "topic_tags": [
                        tag["name"] for tag in question.get("topicTags", [])
                    ],
                    "hints": question.get("hints", []),
                    "examples": question.get("exampleTestcaseList", []),
                    "sample_test_case": question.get("sampleTestCase", ""),
                }
                
        except Exception as e:
            logger.error(f"Error fetching problem '{title_slug}': {e}")
            return None


# Singleton instance
leetcode_service = LeetCodeService()
