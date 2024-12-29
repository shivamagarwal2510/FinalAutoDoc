from typing import List
from ..models.schemas import DocumentationChange

def extract_documentation_changes(content: str) -> List[DocumentationChange]:
    """
    Extract documentation changes from XML-like content, even if the XML is malformed or has extra content.
    
    Args:
        content: String containing XML-like documentation update content
    Returns:
        List of DocumentationChange objects
    """
    changes = []
    
    # Find the main <changes> section
    changes_start = content.find("<changes>")
    changes_end = content.find("</changes>")
    
    if changes_start == -1 or changes_end == -1:
        return changes
    
    changes_content = content[changes_start:changes_end]
    
    # Find individual change blocks
    while "<change" in changes_content:
        # Extract single change block
        change_start = changes_content.find("<change")
        change_end = changes_content.find("</change>", change_start) + len("</change>")
        if change_end == -1:
            break
            
        change_block = changes_content[change_start:change_end]
        
        # Extract change attributes
        change_type = _extract_between(change_block, 'type="', '"')
        file_path = _extract_between(change_block, 'file_path="', '"')
        original_content = _extract_between(change_block, "<original_content>", "</original_content>")
        suggested_content = _extract_between(change_block, "<suggested_content>", "</suggested_content>")
        
        # Create DocumentationChange object
        change = DocumentationChange(
            change_type=change_type,
            file_path=file_path,
            original_content=original_content if original_content else None,
            suggested_content=suggested_content if suggested_content else None
        )
        changes.append(change)
        
        # Move to next change block
        changes_content = changes_content[change_end:]
    
    return changes

def _extract_between(text: str, start_marker: str, end_marker: str) -> str:
    """Helper function to extract content between two markers"""
    start = text.find(start_marker)
    if start == -1:
        return ""
    start += len(start_marker)
    end = text.find(end_marker, start)
    if end == -1:
        return ""
    return text[start:end].strip()



