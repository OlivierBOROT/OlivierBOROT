import requests
import re
import os
import matplotlib.pyplot as plt

# --------------------------------------------------
# Configuration
# --------------------------------------------------

USERNAME = "OlivierBOROT"

README_FILE = "README.md"
START_TAG = "<!--DYNAMIC_SECTION_START-->"
END_TAG = "<!--DYNAMIC_SECTION_END-->"

API_BASE = "https://api.github.com"


# --------------------------------------------------
# Fetch all repositories
# --------------------------------------------------
def get_repos() -> list:
    """Fetch all repositories for the given user.

    Returns:
        list: A list of repositories.
    """
    res = requests.get(f"{API_BASE}/users/{USERNAME}/repos?per_page=100")
    res.raise_for_status()
    return res.json()


# --------------------------------------------------
# Fetch commit count for a single repository
# --------------------------------------------------
def get_commit_count(repo_name: str) -> int:
    """Fetch the total commit count for the given repository.

    Args:
        repo_name (str): The name of the repository.

    Returns:
        int: The total commit count for the repository.
    """
    url = f"{API_BASE}/repos/{USERNAME}/{repo_name}/stats/contributors"
    r = requests.get(url, timeout=20)

    if r.status_code == 202:
        return 0

    try:
        data = r.json()
    except ValueError:
        return 0

    if not isinstance(data, list):
        return 0

    for contributor in data:
        if contributor.get("author", {}).get("login") == USERNAME:
            return contributor.get("total", 0)

    return 0


# --------------------------------------------------
# Build the markdown section
# --------------------------------------------------
def generate_section(repos: list) -> str:
    """Generate the markdown section for the README.

    Args:
        repos (list): List of repositories.

    Returns:
        str: The generated markdown section.
    """
    # ----- Latest repos -----
    recent = sorted(repos, key=lambda r: r["pushed_at"], reverse=True)[:5]

    text = "### ⏱ Latest Repositories\n"
    for r in recent:
        date = r["pushed_at"].split("T")[0]
        text += f"- [{r['name']}]({r['html_url']}) – updated {date}\n"

    # ----- Most active repos -----
    text += "\n### 📊 Most Active (by commits)\n"

    repo_commit_data = []

    for r in repos:
        commits = get_commit_count(r["name"])
        repo_commit_data.append((r, commits))

    most_active = sorted(repo_commit_data, key=lambda x: x[1], reverse=True)[:5]

    for repo, commits in most_active:
        text += f"- [{repo['name']}]({repo['html_url']}) – {commits} commits\n"

    return text


# --------------------------------------------------
# Apply section to README
# --------------------------------------------------
def update_readme(new_content: str) -> None:
    """Update the README file with the new dynamic section.

    Args:
        new_content (str): The new content to insert into the README.
    """
    with open(README_FILE, "r", encoding="utf-8") as f:
        readme = f.read()

    block = f"{START_TAG}\n{new_content}\n{END_TAG}"

    if START_TAG in readme:
        # Replace existing section
        readme = re.sub(
            f"{START_TAG}[\\s\\S]*{END_TAG}",
            block,
            readme,
        )
    else:
        # Append if missing
        readme += "\n" + block

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme)


# --------------------------------------------------
# Generate language usage chart
# --------------------------------------------------
def generate_language_chart(repos) -> None:
    """Generate a bar chart of the top programming languages used across repositories.

    Args:
        repos (list): List of repositories.
    """
    lang_totals = {}

    # Sum bytes per language from GitHub API
    for r in repos:
        url = f"https://api.github.com/repos/{USERNAME}/{r['name']}/languages"
        res = requests.get(url, timeout=20)
        if res.status_code != 200:
            continue
        langs = res.json()
        for lang, count in langs.items():
            lang_totals[lang] = lang_totals.get(lang, 0) + count

    # Top 5 languages
    sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:5]

    total = sum(v for _, v in sorted_langs)
    langs = [l for l, _ in sorted_langs]
    values = [(v / total) * 100 for _, v in sorted_langs]

    # Plot
    plt.figure(figsize=(8, 4))
    bars = plt.bar(langs, values)
    plt.title("Most used programming languages in my public repositories")
    plt.ylabel("Percentage (%)")
    plt.ylim(0, max(values) + 5)

    for bar, v in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 f"{v:.1f}%", ha="center", va="bottom")

    # Save image
    os.makedirs("charts", exist_ok=True)
    plt.tight_layout()
    plt.savefig("charts/top_languages.png")
    plt.close()



# --------------------------------------------------
# Main
# --------------------------------------------------
def main() -> None:
    """Main function to update the README with dynamic repository information."""
    repos = get_repos()
    
    # Generate charts
    generate_language_chart(repos)
    new_data = generate_section(repos)
    update_readme(new_data)


if __name__ == "__main__":
    main()
