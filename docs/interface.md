# Profile interface

`modules.profile.build_profile(form_data: dict | None = None, skills: list[str] | str | None = None) -> dict`

## Input

`form_data` accepts these optional keys:

| Key | Type | Behavior |
| --- | --- | --- |
| `skills` | `str` or list of strings | Skills typed in the Skills field. String values are separated by commas, semicolons, or line breaks. An explicit `skills` argument overrides this key. |
| `interests` | `str` or list of strings | Interests, split by commas, semicolons, or line breaks. |
| `experience` | `str` | Free-form experience text. Whitespace is collapsed; commas are preserved and are not used as separators. |

Both arguments may be `None`; missing values and an empty mapping produce an empty profile. Skill names are normalized against the sample data in `Data/roles.json`, `Data/resources.json`, and the keywords in `Data/interview_questions.json`. `modules.skill_extractor.normalize_skill(value: str | None) -> str | None` returns a canonical skill name, including the `py` alias for `Python`, or `None` when it cannot recognize a skill.

The Skills field also accepts entries prefixed by `interesting:`, `interest:`, or `sở thích:`. Those entries are moved to interests and reported in `moved` so the interface can show a message and offer an undo action.

## Output

The returned dictionary always contains:

| Key | Type | Behavior |
| --- | --- | --- |
| `skills` | `list[str]` | Canonical recognized skills plus unrecognized entries the user may choose to keep. Deduplicated and sorted case-insensitively. |
| `interests` | `list[str]` | Cleaned and deduplicated interest entries, including items moved from Skills. |
| `experience` | `str` | Cleaned free-form text; internal whitespace is collapsed, while commas remain intact. |
| `unrecognized_skills` | `list[str]` | Entries not found in the sample skill catalog. These are also retained in `skills` until the user chooses to remove them. |
| `moved` | `list[dict[str, str]]` | Each item has `item`, `from`, and `to` keys, for example `{"item": "play games", "from": "Kỹ năng", "to": "Sở thích"}`. |

The Streamlit app reads role choices from `Data/roles.json`. Course recommendations come from `Data/resources.json`; interview questions are grouped by role in `Data/interview_questions.json`. The skill catalog uses the role requirements, learning-resource skills, and interview keywords, with paths resolved relative to the project rather than the current working directory.
