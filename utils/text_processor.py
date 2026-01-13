from utils.constants import DEFAULT_SECTION_NAMES

section_aliases = {
    "治療内容": "治療経過",
    "その他": "備考",
    "補足": "備考",
    "メモ": "備考"
}


def format_output_summary(summary_text):
    processed_text = (
        summary_text.replace('*', '')
        .replace('＊', '')
        .replace('#', '')
        .replace(' ', '')
    )
    return processed_text


def parse_output_summary(summary_text):
    sections = {section: "" for section in DEFAULT_SECTION_NAMES}
    lines = summary_text.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        found_section = False

        # 各セクション名をチェック
        for section in DEFAULT_SECTION_NAMES:
            # コロンありの場合（診断名: 高血圧症）
            if line.startswith(section + ":") or line.startswith(section + "："):
                current_section = section
                content = line.replace(section + ":", "").replace(section + "：", "").strip()
                sections[current_section] = content
                found_section = True
                break
            # コロンなしの場合（診断名 高血圧症）
            elif line.startswith(section + " ") and len(line.split()) >= 2:
                current_section = section
                content = line.replace(section, "", 1).strip()
                sections[current_section] = content
                found_section = True
                break

        # エイリアスをチェック
        if not found_section:
            for alias, target_section in section_aliases.items():
                if line.startswith(alias + ":") or line.startswith(alias + "："):
                    current_section = target_section
                    content = line.replace(alias + ":", "").replace(alias + "：", "").strip()
                    sections[current_section] = content
                    found_section = True
                    break
                elif line.startswith(alias + " ") and len(line.split()) >= 2:
                    current_section = target_section
                    content = line.replace(alias, "", 1).strip()
                    sections[current_section] = content
                    found_section = True
                    break

        # セクションが既に設定されていて、新しいセクションが見つからない場合は、現在のセクションに内容を追加
        if current_section and not found_section:
            if sections[current_section]:
                sections[current_section] += "\n" + line
            else:
                sections[current_section] = line

    return sections
