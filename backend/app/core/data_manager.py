"""Utility classes to maniuplate GitHub repositories."""

import logging
import os
from abc import abstractmethod
from functools import cached_property
from typing import Any, Dict, Generator, Tuple, List
import subprocess
import time
import requests
from git import GitCommandError, Repo
from backend.app.models.schemas import DocumentationChange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DataManager:
    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id

    @abstractmethod
    def download(self) -> bool:
        """Downloads the data from a remote location."""

    @abstractmethod
    def walk(self) -> Generator[Tuple[Any, Dict], None, None]:
        """Yields a tuple of (data, metadata) for each data item in the dataset."""


class GitHubRepoManager(DataManager):
    """Class to manage a local clone of a GitHub repository."""

    def __init__(
        self,
        repo_id: str,
        commit_hash: str = None,
        access_token: str = None,
        local_dir: str = None,
        inclusion_file: str = None,
        exclusion_file: str = None,
        doc_target_path: str = None
    ):
        """
        Args:
            repo_id: The identifier of the repository in owner/repo format, e.g. "Storia-AI/sage".
            commit_hash: Optional commit hash to checkout. If not specified, we pull the latest version of the repo.
            access_token: A GitHub access token to use for cloning private repositories. Not needed for public repos.
            local_dir: The local directory where the repository will be cloned.
            inclusion_file: A file with a lists of files/directories/extensions to include. Each line must be in one of
                the following formats: "ext:.my-extension", "file:my-file.py", or "dir:my-directory".
            exclusion_file: A file with a lists of files/directories/extensions to exclude. Each line must be in one of
                the following formats: "ext:.my-extension", "file:my-file.py", or "dir:my-directory".
        """
        super().__init__(dataset_id=repo_id)
        self.repo_id = repo_id
        self.commit_hash = commit_hash
        self.access_token = access_token
        self.doc_target_path = doc_target_path

        self.local_dir = local_dir or "/tmp/"
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir)
        self.local_path = os.path.join(self.local_dir, repo_id)

        self.log_dir = os.path.join(self.local_dir, "logs", repo_id)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        if inclusion_file and exclusion_file:
            raise ValueError("Only one of inclusion_file or exclusion_file should be provided.")

        self.inclusions = self._parse_filter_file(inclusion_file) if inclusion_file else None
        self.exclusions = self._parse_filter_file(exclusion_file) if exclusion_file else None

    @cached_property
    def is_public(self) -> bool:
        """Checks whether a GitHub repository is publicly visible."""
        response = requests.get(f"https://api.github.com/repos/{self.repo_id}", timeout=10)
        # Note that the response will be 404 for both private and non-existent repos.
        return response.status_code == 200

    @cached_property
    def default_branch(self) -> str:
        """Fetches the default branch of the repository from GitHub."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.access_token:
            headers["Authorization"] = f"token {self.access_token}"

        response = requests.get(f"https://api.github.com/repos/{self.repo_id}", headers=headers)
        if response.status_code == 200:
            branch = response.json().get("default_branch", "main")
        else:
            # This happens sometimes when we exceed the Github rate limit. The best bet in this case is to assume the
            # most common naming for the default branch ("main").
            logging.warn(f"Unable to fetch default branch for {self.repo_id}: {response.text}")
            branch = "main"
        return branch

    def download(self) -> bool:
        """Clones the repository to the local directory, if it's not already cloned."""
        if os.path.exists(self.local_path):
            # The repository is already cloned.
            return True

        if not self.is_public and not self.access_token:
            raise ValueError(f"Repo {self.repo_id} is private or doesn't exist.")

        if self.access_token:
            clone_url = f"https://{self.access_token}@github.com/{self.repo_id}.git"
        else:
            clone_url = f"https://github.com/{self.repo_id}.git"
        
        print("Self.doc_target_path: ", self.doc_target_path)
        try:
            if self.doc_target_path:
                 # Initialize an empty repo
                os.makedirs(self.local_path, exist_ok=True)
                subprocess.run(["git", "init"], cwd=self.local_path, check=True)
                
                # Add remote
                subprocess.run(
                    ["git", "remote", "add", "origin", clone_url],
                    cwd=self.local_path,
                    check=True
                )

                # Enable sparse-checkout
                subprocess.run(
                    ["git", "config", "core.sparseCheckout", "true"],
                    cwd=self.local_path,
                    check=True
                )

                # Clean and normalize the doc_target_path
                clean_path = self.doc_target_path.strip('/')
                
                # Set up sparse-checkout patterns
                sparse_checkout_path = os.path.join(self.local_path, ".git", "info", "sparse-checkout")
                with open(sparse_checkout_path, "w") as f:
                    # Add the exact path and any subdirectories
                    f.write(f"{clean_path}/*\n")
                    # Also include the directory itself
                    f.write(f"{clean_path}\n")

                # Fetch and checkout the default branch
                print(f"Fetching documentation from path: {clean_path}")
                subprocess.run(
                    ["git", "pull", "origin", self.default_branch, "--depth=1"],
                    cwd=self.local_path,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Verify the directory exists after clone
                doc_path = os.path.join(self.local_path, clean_path)
                if not os.path.exists(doc_path):
                    raise ValueError(f"Documentation path {clean_path} not found in repository")
                
                print(f"Successfully cloned documentation folder: {clean_path}")
                return True
            elif self.commit_hash:
                print("Clonining with self.commit_hash")
                repo = Repo.clone_from(clone_url, self.local_path)
                repo.git.checkout(self.commit_hash)
            else:
                print("cloining in the else block")
                Repo.clone_from(clone_url, self.local_path, depth=1, single_branch=True)
        except GitCommandError as e:
            logging.error("Unable to clone %s from %s. Error: %s", self.repo_id, clone_url, e)
            return False
        return True

    def _parse_filter_file(self, file_path: str) -> bool:
        """Parses a file with files/directories/extensions to include/exclude.

        Lines are expected to be in the format:
        # Comment that will be ignored, or
        ext:.my-extension, or
        file:my-file.py, or
        dir:my-directory
        """
        with open(file_path, "r") as f:
            lines = f.readlines()

        parsed_data = {"ext": [], "file": [], "dir": []}
        for line in lines:
            if line.startswith("#"):
                # This is a comment line.
                continue
            key, value = line.strip().split(":")
            if key in parsed_data:
                parsed_data[key].append(value)
            else:
                logging.error("Unrecognized key in line: %s. Skipping.", line)

        return parsed_data

    def _should_include(self, file_path: str) -> bool:
        """Checks whether the file should be indexed."""
        # Exclude symlinks.
        if os.path.islink(file_path):
            return False

        # Exclude hidden files and directories.
        if any(part.startswith(".") for part in file_path.split(os.path.sep)):
            return False
        
        if(self.doc_target_path == None):
            # Get file extension
            _, extension = os.path.splitext(file_path)
            extension = extension.lower()

            # List of extensions to exclude
            excluded_extensions = {
                # Binary and media files
                '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pdf', 
                '.zip', '.tar', '.gz', '.rar',
                # Generated files
                '.min.js', '.min.css', '.map', '.lock',
                # Build artifacts
                '.pyc', '.pyo', '.pyd', '.so', '.dll', '.class',
                # Test files
                '.spec.ts', '.spec.js', '.test.ts', '.test.js', 
                '.spec.tsx', '.spec.jsx', '.test.tsx', '.test.jsx',
                '.spec.py', '.test.py',
                # Other
                '.log', '.cache', ".ttf", ".mdx", ".mts", ".lockb",
                '.yaml', '.md'
            }

            # Exclude files with unwanted extensions
            if extension in excluded_extensions:
                return False

            # Exclude specific filenames
            excluded_filenames = {
                'package-lock.json', 'yarn.lock', 'poetry.lock',
                '.gitignore', '.dockerignore', '.env',
                'package.json'
            }
            if os.path.basename(file_path) in excluded_filenames:
                return False

            # Exclude specific directories
            excluded_dirs = {
                'node_modules', 'dist', 'build', 'target',
                'venv', 'env', '.git', '__pycache__',
                '__registry__', 'tests', 'test', '__tests__',
                '__test__', 'spec', '__spec__'
            }
            if any(d in file_path.split(os.path.sep) for d in excluded_dirs):
                return False

        # If we have explicit inclusions/exclusions, use them
        if self.inclusions or self.exclusions:
            file_name = os.path.basename(file_path)
            dirs = os.path.dirname(file_path).split("/")

            if self.inclusions:
                return (
                    extension in self.inclusions.get("ext", [])
                    or file_name in self.inclusions.get("file", [])
                    or any(d in dirs for d in self.inclusions.get("dir", []))
                )
            elif self.exclusions:
                return (
                    extension not in self.exclusions.get("ext", [])
                    and file_name not in self.exclusions.get("file", [])
                    and all(d not in dirs for d in self.exclusions.get("dir", []))
                )

        return True

    def walk(self, get_content: bool = True) -> Generator[Tuple[Any, Dict], None, None]:
        """Walks the local repository path and yields a tuple of (content, metadata) for each file.
        The filepath is relative to the root of the repository (e.g. "org/repo/your/file/path.py").

        Args:
            get_content: When set to True, yields (content, metadata) tuples. When set to False, yields metadata only.
        """
        # We will keep appending to these files during the iteration, so we need to clear them first.
        repo_name = self.repo_id.replace("/", "_")
        included_log_file = os.path.join(self.log_dir, f"included_{repo_name}.txt")
        excluded_log_file = os.path.join(self.log_dir, f"excluded_{repo_name}.txt")
        if os.path.exists(included_log_file):
            os.remove(included_log_file)
            logging.info("Logging included files at %s", included_log_file)
        if os.path.exists(excluded_log_file):
            os.remove(excluded_log_file)
            logging.info("Logging excluded files at %s", excluded_log_file)

        for root, _, files in os.walk(self.local_path):
            file_paths = [os.path.join(root, file) for file in files]
            included_file_paths = [f for f in file_paths if self._should_include(f)]

            with open(included_log_file, "a") as f:
                for path in included_file_paths:
                    f.write(path + "\n")

            excluded_file_paths = set(file_paths).difference(set(included_file_paths))
            with open(excluded_log_file, "a") as f:
                for path in excluded_file_paths:
                    f.write(path + "\n")

            for file_path in included_file_paths:
                relative_file_path = file_path[len(self.local_dir) + 1 :]
                metadata = {
                    "file_path": relative_file_path,
                    "url": self.url_for_file(relative_file_path),
                }

                if not get_content:
                    yield metadata
                    continue

                contents = self.read_file(relative_file_path)
                if contents:
                    yield contents, metadata

    def url_for_file(self, file_path: str) -> str:
        """Converts a repository file path to a GitHub link."""
        file_path = file_path[len(self.repo_id) + 1 :]
        return f"https://github.com/{self.repo_id}/blob/{self.default_branch}/{file_path}"

    def read_file(self, relative_file_path: str) -> str:
        """Reads the contents of a file in the repository."""
        absolute_file_path = os.path.join(self.local_dir, relative_file_path)
        with open(absolute_file_path, "r") as f:
            try:
                contents = f.read()
                return contents
            except UnicodeDecodeError:
                logging.warning("Unable to decode file %s.", absolute_file_path)
                return None

    def from_args(args: Dict):
        """Creates a GitHubRepoManager from command-line arguments and clones the underlying repository."""
        repo_manager = GitHubRepoManager(
            repo_id=args["repo_id"],
            commit_hash=args.get("commit_hash"),
            access_token=args.get("access_token") or os.getenv("GITHUB_TOKEN"),
            local_dir=args["local_dir"],
            inclusion_file=args.get("inclusion_file"),
            exclusion_file=args.get("exclusion_file"),
            doc_target_path=args.get("doc_target_path")
        )
        success = repo_manager.download()
        if not success:
            raise ValueError(
                f"Unable to clone. Please check that it exists and you have access to it. "
                "For private repositories, please set the GITHUB_TOKEN variable in your environment."
            )
        return repo_manager
    
    def create_documentation_pr(self, changes: List[DocumentationChange], branch_prefix: str = "docs-update") -> str:
        """
        Creates a pull request with documentation changes.
        
        Args:
            changes: List[DocumentationChange] objects containing change_type, file_path, 
                    original_content, and suggested_content
            branch_prefix: Prefix for the new branch name
            
        Returns:
            str: URL of the created pull request
        """
        print("create_documentation_pr")
        
        try:
            # Create a new branch
            branch_name = f"{branch_prefix}-{int(time.time())}"
            repo = Repo(self.local_path)
            
            # Fetch and checkout the default branch
            origin = repo.remote('origin')
            origin.fetch()
            repo.git.checkout(self.default_branch)
            repo.git.reset('--hard', 'HEAD')
            repo.git.pull()
            
            # Create and checkout new branch from default branch
            current = repo.create_head(branch_name)
            current.checkout()
            print("Checked out to the new branch", branch_name)
            
            modified_files = []
            # Group changes by file to process them together
            changes_by_file = {}
            for change in changes:
                if change.file_path not in changes_by_file:
                    changes_by_file[change.file_path] = []
                changes_by_file[change.file_path].append(change)
            
            for file_path, file_changes in changes_by_file.items():
                clean_file_path = file_path.replace(self.repo_id + '/', "").replace("\\", "/")
                abs_file_path = os.path.join(self.local_path, clean_file_path)
                
                # Handle new file creation
                if any(change.change_type == "new_file" for change in file_changes):
                    new_file_change = next(change for change in file_changes if change.change_type == "new_file")
                    os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
                    with open(abs_file_path, 'wb') as f:
                        # Write in binary mode to preserve exact content
                        f.write(new_file_change.suggested_content.encode('utf-8'))
                    repo.index.add([clean_file_path])
                    modified_files.append(f"Created {file_path}")
                    continue
                
                # Handle existing files
                if os.path.exists(abs_file_path):
                    # Read file content in binary mode to preserve exact format
                    with open(abs_file_path, 'rb') as f:
                        file_content_bytes = f.read()
                    
                    try:
                        file_content = file_content_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # If UTF-8 decoding fails, try with error replacement
                        file_content = file_content_bytes.decode('utf-8', errors='replace')
                    
                    # Process the changes one by one
                    changes_made = False
                    
                    # Sort changes to process replacements first
                    for change in sorted(file_changes, key=lambda c: 0 if c.change_type == "replace" else 1):
                        if change.change_type == "delete":
                            # For delete operations, handle character-by-character to preserve line endings
                            if change.original_content in file_content:
                                # Carefully preserve exact format during deletion
                                start_pos = file_content.find(change.original_content)
                                end_pos = start_pos + len(change.original_content)
                                file_content = file_content[:start_pos] + file_content[end_pos:]
                                changes_made = True
                                modified_files.append(f"Deleted content from {file_path}")
                            else:
                                logging.warning(f"Original content not found in {file_path} for deletion. Skipping.")
                        
                        elif change.change_type == "replace":
                            # Process replacement with careful handling of line endings
                            if change.original_content in file_content:
                                # Get exact bytes for original and replacement to preserve format
                                original_bytes = change.original_content.encode('utf-8')
                                suggested_bytes = change.suggested_content.encode('utf-8')
                                
                                # Find exact position in original content
                                start_pos = file_content.find(change.original_content)
                                end_pos = start_pos + len(change.original_content)
                                
                                # Perform the replacement preserving exact context
                                file_content = file_content[:start_pos] + change.suggested_content + file_content[end_pos:]
                                changes_made = True
                                modified_files.append(f"Updated {file_path}")
                            else:
                                # Try a more precise line-by-line matching approach
                                original_lines = change.original_content.splitlines()
                                file_lines = file_content.splitlines()
                                
                                # Search for an exact match of all lines together
                                found_match = False
                                
                                for i in range(len(file_lines) - len(original_lines) + 1):
                                    match = True
                                    for j, original_line in enumerate(original_lines):
                                        # Compare stripped lines to handle whitespace differences
                                        if original_line.strip() != file_lines[i + j].strip():
                                            match = False
                                            break
                                    
                                    if match:
                                        # Keep the original line endings by preserving the file structure
                                        # but replace the actual content
                                        suggested_lines = change.suggested_content.splitlines()
                                        
                                        # Reconstruct the file content with the replacement
                                        new_lines = file_lines[:i] + suggested_lines + file_lines[i + len(original_lines):]
                                        
                                        # Detect the line ending style used in the file
                                        line_ending = '\n'  # Default to Unix-style
                                        if '\r\n' in file_content:
                                            line_ending = '\r\n'  # Windows-style
                                        
                                        # Join with the detected line ending
                                        file_content = line_ending.join(new_lines)
                                        
                                        changes_made = True
                                        found_match = True
                                        modified_files.append(f"Updated {file_path} (line-by-line)")
                                        break
                                
                                if not found_match:
                                    logging.warning(f"Original content not found in {file_path} for replacement. Skipping.")
                        
                        elif change.change_type == "append":
                            # For append operations, precisely locate the append point
                            if change.original_content in file_content:
                                position = file_content.find(change.original_content) + len(change.original_content)
                                file_content = file_content[:position] + change.suggested_content + file_content[position:]
                                changes_made = True
                                modified_files.append(f"Appended to {file_path}")
                            else:
                                logging.warning(f"Append point not found in {file_path}. Skipping.")
                    
                    if changes_made:
                        # Write the updated content back to the file in binary mode to preserve format
                        with open(abs_file_path, 'wb') as f:
                            f.write(file_content.encode('utf-8'))
                        repo.index.add([clean_file_path])
                else:
                    logging.warning(f"File {file_path} does not exist. Skipping changes.")
            
            if not modified_files:
                return None
            
            print("Modified files:", modified_files)
            
            # Commit changes
            commit_message = "Update documentation based on recent code changes\n\n" + "\n".join(modified_files)
            repo.index.commit(commit_message)
            
            # Push changes
            origin.push(branch_name)
            print("Pushed the changes to the new branch", branch_name)

            # Create PR using GitHub API
            headers = {
                "Authorization": f"token {self.access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            pr_data = {
                "title": "Documentation Updates",
                "body": "Automated documentation updates based on recent code changes:\n\n" + "\n".join(modified_files),
                "head": branch_name,
                "base": self.default_branch,
                "maintainer_can_modify": True,
                "draft": False
            }
            
            response = requests.post(
                f"https://api.github.com/repos/{self.repo_id}/pulls",
                headers=headers,
                json=pr_data
            )
            
            if response.status_code != 201:
                raise GitCommandError(
                    "create_pr", 
                    f"Failed to create PR: {response.json().get('message', 'Unknown error')}"
                )
                
            return response.json()["html_url"]

        except Exception as e:
            logging.error(f"Error creating PR: {str(e)}")
            raise