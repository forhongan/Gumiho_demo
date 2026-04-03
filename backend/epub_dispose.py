import os
import json
import re
from Config import Config


class EpubDispose:
    """EPUB 生成与处理类

    初始化参数:
        project_path (str): 项目路径, 可为 None
    """
    def __init__(self, project_path=None):
        self.project_path = project_path
    
    def epub_refilled(self, epub_file_path, translated_file_path=None, novel_status="f_trans_finished", with_original_text_or_not=False):
        """
        回填译文到原始 EPUB 文件中。
        translated_file_path: TranslateFile.json 路径
        with_original_text_or_not: False -> 用译文替换原文段落；True -> 在原文段落后插入译文段落
        返回写入的 epub 跂径
        """
        try:
            from ebooklib import epub
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("请先安装 ebooklib 和 beautifulsoup4: pip install ebooklib beautifulsoup4")

        if not epub_file_path or not os.path.exists(epub_file_path):
            raise FileNotFoundError(f"EPUB 文件未找到: {epub_file_path}")

        if not translated_file_path or not os.path.exists(translated_file_path):
            raise FileNotFoundError(f"翻译文件未找到: {translated_file_path}")

        # 读取翻译 JSON
        with open(translated_file_path, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)

        chapters = translated_data.get("chapters", [])
        title = translated_data.get("title", "")

        # 获取翻译信息标签
        get_tag_by_config = Config(config_path=os.path.join(self.project_path, "config.yml")) if self.project_path else Config(config_path=os.path.join(os.getcwd(), "config.yml"))
        try:
            tag = get_tag_by_config.make_translation_info_tags(status='translating')
        except Exception:
            tag = None

        # 读取 EPUB
        book = epub.read_epub(epub_file_path)

        # 获取 HTML 项目
        html_items = []
        for item in book.get_items_of_type(epub.EpubHtml):
            html_items.append(item)

        # 回退：有些 EPUB 的文档未被识别为 epub.EpubHtml（ebooklib 版本差异或特殊打包方式）
        if not html_items:
            print("DEBUG: epub.EpubHtml 未返回项，尝试回退遍历所有项目以查找可读内容")
            try:
                all_items = list(book.get_items())
                print(f"DEBUG: book.get_items() 总项数: {len(all_items)}; 前10 类型样例: {[type(it).__name__ for it in all_items[:10]]}")
                for item in all_items:
                    # 尝试读取内容
                    content = None
                    try:
                        if hasattr(item, 'get_body_content'):
                            content = item.get_body_content()
                        elif hasattr(item, 'get_content'):
                            content = item.get_content()
                    except Exception:
                        content = None
                    if isinstance(content, bytes):
                        try:
                            content = content.decode('utf-8', errors='ignore')
                        except Exception:
                            content = None
                    if content and isinstance(content, str) and content.strip():
                        html_items.append(item)
            except Exception as ex:
                print(f"DEBUG: 回退遍历 book.get_items() 时出错: {ex}")
        print(f"DEBUG: 收集到 html_items: {len(html_items)}")

        # 记忆上一次匹配的索引
        last_matched_index = 0

        def clean_text(text):
            import re
            return re.sub(r'\s+', ' ', text.strip())

        # 调试：收集所有提取的文本
        all_extracted_texts = []

        # 辅助函数：提取段落（类似 epub_format）
        def _extract_paragraphs_from_html(soup):
            # 移除不可见内容
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            # 处理 ruby
            for rt in soup.find_all('rt'):
                rt.decompose()
            for ruby in soup.find_all('ruby'):
                ruby.unwrap()
            # 处理 br
            for br in soup.find_all('br'):
                br.replace_with('\n')

            parts = []
            # 简化：直接搜索整个 soup
            search_roots = [soup]
            print(f"DEBUG: search_roots: {len(search_roots)}")
            for root in search_roots:
                if not root:
                    continue
                # 扩展标签列表（保持原逻辑，避免某些结构 EPUB 解析不完备）
                tags_to_find = ['p', 'div', 'section', 'article', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'span', 'em', 'strong', 'b', 'i', 'u', 'a', 'td', 'th']
                for tag in root.find_all(tags_to_find):
                    text = tag.get_text(separator='', strip=True)
                    if text:
                        is_title = tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                        parts.append({'text': text, 'tag': tag, 'is_title': is_title})

            if not parts:
                print("DEBUG: No parts found, using fallback")
                text_only = soup.get_text('\n')
                snippet = text_only[:200].replace('\n', '\\n')
                print(f"DEBUG: text_only length: {len(text_only)}, snippet: {snippet}")
                raw_parts = re.split(r'\n\s*\n', text_only)
                for p in raw_parts:
                    t = re.sub(r'\s+', ' ', p).strip()
                    if t:
                        parts.append({'text': t, 'tag': None, 'is_title': False})

            cleaned = []
            for item in parts:
                p = item['text']
                p2 = p.replace('\r', '').replace('\xa0', ' ').strip()
                p2 = re.sub(r'\s+', ' ', p2)
                # 放松过滤：只检查长度
                if len(p2) >= 1:
                    cleaned.append({'text': p2, 'tag': item['tag'], 'is_title': item.get('is_title', False)})
                    all_extracted_texts.append(p2)  # 调试收集
            print(f"DEBUG: Cleaned parts: {len(cleaned)}")
            return cleaned

        # 遍历每个 HTML 项目
        for item in html_items:
            try:
                content = item.get_body_content()
            except AttributeError:
                continue
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'lxml')

            inserted_pairs = set()

            # 如果是第一个 HTML 项目，添加翻译信息标签
            if item == html_items[0] and tag:
                print(f"DEBUG: Inserting translation info tag into first HTML item")
                print(f"DEBUG: Tag content: {tag}") 
                new_p = soup.new_tag('p', style="margin-top: 2em; font-style: italic;")
                new_p.string = tag
                if soup.body:
                    soup.body.insert(0, new_p)
                else:
                    soup.insert(0, new_p)

            # 提取段落
            paragraphs = _extract_paragraphs_from_html(soup)

            # 对于每个段落，尝试匹配
            for para in paragraphs:
                text = clean_text(para['text'])
                tag = para['tag']

                if not text or not tag:
                    continue

                # 搜索匹配
                found = False
                for i in range(last_matched_index, len(chapters)):
                    chap = chapters[i]
                    orig = clean_text(chap.get("original-text", ""))
                    if orig == text:
                        trans = chap.get("translation-text", "")
                        if trans:
                            if with_original_text_or_not:
                                pair_key = (orig, trans)
                                if pair_key in inserted_pairs:
                                    last_matched_index = i + 1
                                    found = True
                                    break
                                inserted_pairs.add(pair_key)
                                new_tag = soup.new_tag('p')
                                new_tag.string = trans
                                tag.insert_after(new_tag)
                            else:
                                tag.string = trans
                        last_matched_index = i + 1
                        found = True
                        break

                if not found:
                    # 从头搜索
                    for i in range(last_matched_index):
                        chap = chapters[i]
                        orig = clean_text(chap.get("original-text", ""))
                        if orig == text:
                            trans = chap.get("translation-text", "")
                            if trans:
                                if with_original_text_or_not:
                                    pair_key = (orig, trans)
                                    if pair_key in inserted_pairs:
                                        last_matched_index = i + 1
                                        break
                                    inserted_pairs.add(pair_key)
                                    new_tag = soup.new_tag('p')
                                    new_tag.string = trans
                                    tag.insert_after(new_tag)
                                else:
                                    tag.string = trans
                            last_matched_index = i + 1
                            break

            # 更新项目内容
            item.content = str(soup)

        # 调试：输出前一千条文本到 output.txt
        # with open('1111output.txt', 'w', encoding='utf-8') as f:
        #     for i, txt in enumerate(all_extracted_texts[:1000]):
        #         f.write(f"{i+1}: {txt}\n")

        # 生成文件名
        base_name = f'Gumiho-{title.strip()}-refilled-'
        status = "初译完成" if novel_status == "f_trans_finished" else "校对完成"
        file_name = base_name + status + '.epub'

        if self.project_path:
            save_dir = os.path.join(self.project_path, 'result')
            os.makedirs(save_dir, exist_ok=True)
        else:
            save_dir = os.path.dirname(epub_file_path)

        save_path = os.path.join(save_dir, file_name)

        # 写入 EPUB 文件
        epub.write_epub(save_path, book, {})

        print(f"DEBUG: EPUB saved to {save_path}")

        return save_path

    def normal_epub_rebuild(self, start_idx, end_chapter_idx, translated_file_path=None, novel_status="f_trans_finished", with_original_text_or_not=False, cover=None):
        """
        将翻译后的JSON文件重新构建为EPUB格式电子书，包含章节结构和目录。
        返回：写入的文件路径。
        """
        try:
            from ebooklib import epub
        except ImportError:
            raise ImportError("请先安装 ebooklib: pip install ebooklib")

        translated_file_path = translated_file_path if translated_file_path else None

        # 读取翻译 JSON
        if not translated_file_path or not os.path.exists(translated_file_path):
            raise FileNotFoundError(f"翻译文件未找到: {translated_file_path}")
        with open(translated_file_path, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)

        title = translated_data.get("title", "")
        description = translated_data.get("description", "")
        chapters = translated_data.get("chapters", [])

        # 验证索引
        try:
            s = int(start_idx)
            e = int(end_chapter_idx)
        except Exception:
            raise ValueError("start_idx 和 end_chapter_idx 必须为整数")
        if s > e:
            raise ValueError("start_idx 不能大于 end_chapter_idx")

        # 过滤并按 id 排序出指定 id 范围内的章节
        selected = sorted([c for c in chapters if isinstance(c.get("id"), int) and s <= c.get("id") <= e], key=lambda x: x.get("id"))
        if not selected:
            raise ValueError("未找到指定范围的章节")

        # 创建 EPUB 书籍对象
        book = epub.EpubBook()

        # 设置元数据
        book.set_identifier(f'gumiho_{title}_{s}_{e}')
        book.set_title(title)
        book.set_language('zh-CN')
        book.add_author('Gumiho Translation')

        # Helper: 修复相邻引号的换行问题
        def _repair_adjacent_quotes(text):
            if not text:
                return text
            s = str(text)
            s = s.replace('』『', '』\n『')
            s = s.replace('」『', '」\n『')
            s = s.replace('』「', '』\n「')
            return s

        # Helper: 将文本转换为HTML段落
        def _text_to_html_paragraphs(text):
            if not text:
                return ""
            lines = str(text).splitlines()
            return ''.join(f'<p>{line}</p>' for line in lines if line.strip())

        # 创建封面页（包含标题和描述）
        intro_content = f'<h1>{title}</h1>'
        if description:
            intro_content += _text_to_html_paragraphs(description)

        # 获取翻译信息标签
        get_tag_by_config = Config(config_path=os.path.join(self.project_path, "config.yml")) if self.project_path else Config(config_path=os.path.join(os.getcwd(), "config.yml"))
        try:
            tag = get_tag_by_config.make_translation_info_tags(status='translating')
        except Exception:
            tag = None
        if tag:
            intro_content += f'<p style="margin-top: 2em; font-style: italic;">{tag}</p>'

        intro_chapter = epub.EpubHtml(title='简介', file_name='intro.xhtml', lang='zh-CN')
        intro_chapter.content = intro_content
        # 空内容保护：确保 intro_chapter.content 非空，否则使用占位符并打印调试信息
        if not (isinstance(intro_chapter.content, str) and intro_chapter.content.strip()):
            print(f"警告: intro_chapter 内容为空，使用占位符。title={title!r}")
            intro_chapter.content = '<p></p>'
        book.add_item(intro_chapter)

        # 解析章节结构
        epub_chapters = []
        toc_entries = []
        spine_entries = ['nav', intro_chapter]

        i = 0
        chapter_counter = 0
        volume_counter = 0

        while i < len(selected):
            item = selected[i]
            item_type = item.get("type", "")

            # 如果是标题
            if isinstance(item_type, str) and item_type.startswith("title"):
                # 检查下一个元素是否也是标题（判断是否为卷标题）
                is_volume_title = False
                if i + 1 < len(selected):
                    next_item = selected[i + 1]
                    next_type = next_item.get("type", "")
                    if isinstance(next_type, str) and next_type.startswith("title"):
                        is_volume_title = True

                if is_volume_title:
                    # 这是卷标题，暂存但不立即创建章节
                    volume_counter += 1
                    volume_title = item.get("translation-text") or item.get("original-text", "")
                    volume_title = _repair_adjacent_quotes(volume_title)
                    volume_toc_entry = []
                    i += 1
                    continue

                # 这是章节标题
                chapter_counter += 1
                chapter_title = item.get("translation-text") or item.get("original-text", "")
                chapter_title = _repair_adjacent_quotes(chapter_title)

                # 收集该章节的所有正文段落
                content_parts = []

                # 如果需要显示原文标题
                if with_original_text_or_not:
                    orig_title = item.get("original-text", "")
                    if orig_title:
                        orig_title = _repair_adjacent_quotes(orig_title)
                        content_parts.append(f'<p style="color: gray;">{orig_title}</p>')

                i += 1

                # 收集正文段落
                while i < len(selected):
                    para_item = selected[i]
                    para_type = para_item.get("type", "")

                    # 遇到下一个标题则停止
                    if isinstance(para_type, str) and para_type.startswith("title"):
                        break

                    # 处理正文段落
                    orig_text = para_item.get("original-text", "")
                    trans_text = para_item.get("translation-text", "")

                    if with_original_text_or_not and orig_text:
                        orig_text = _repair_adjacent_quotes(orig_text)
                        content_parts.append(f'<p style="color: gray;">{orig_text}</p>')

                    text_to_write = trans_text if trans_text else orig_text
                    text_to_write = _repair_adjacent_quotes(text_to_write)
                    if text_to_write:
                        content_parts.append(f'<p>{text_to_write}</p>')

                    i += 1

                # 创建章节HTML
                chapter_html = f'<h2>{chapter_title}</h2>' + ''.join(content_parts)
                chapter_file = epub.EpubHtml(
                    title=chapter_title,
                    file_name=f'chapter_{chapter_counter}.xhtml',
                    lang='zh-CN'
                )
                chapter_file.content = chapter_html
                # 空内容保护：确保章节内容非空，否则使用占位符并打印调试信息
                if not (isinstance(chapter_file.content, str) and chapter_file.content.strip()):
                    print(f"警告: 空章节内容，chapter_id={chapter_counter}, title={chapter_title!r}")
                    chapter_file.content = f'<h2>{chapter_title}</h2><p></p>'
                book.add_item(chapter_file)
                epub_chapters.append(chapter_file)
                spine_entries.append(chapter_file)

                # 添加到目录
                if volume_counter > 0 and 'volume_toc_entry' in locals():
                    volume_toc_entry.append(chapter_file)
                else:
                    toc_entries.append(chapter_file)
            else:
                # 跳过非标题的孤立段落
                i += 1

        # 如果有卷结构，需要重新组织目录
        if volume_counter > 0:
            # 这里需要更复杂的逻辑来处理卷和章节的层级关系
            # 简化处理：如果检测到卷结构，将所有章节按顺序添加
            book.toc = epub_chapters
        else:
            book.toc = toc_entries

        # 添加必需的 NCX 和 Nav 文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # 设置书脊（阅读顺序）
        book.spine = spine_entries

        # 如果提供了封面路径，尝试设置封面
        if cover:
            cover_path = cover
            if os.path.exists(cover_path) and os.path.isfile(cover_path):
                try:
                    with open(cover_path, 'rb') as cf:
                        cover_data = cf.read()
                    cover_name = os.path.basename(cover_path)
                    book.set_cover(cover_name, cover_data)
                except Exception as e:
                    print(f"警告：设置封面失败: {e}")
            else:
                print(f"警告：封面文件不存在: {cover_path}")

        # 生成文件名
        base_name = f'Gumiho-{title.strip()} ({s})-({e})-'
        status = "初译完成" if novel_status == "f_trans_finished" else "校对完成"
        file_name = base_name + status + '.epub'

        if self.project_path:
            save_dir = os.path.join(self.project_path, 'result')
            os.makedirs(save_dir, exist_ok=True)
        else:
            save_dir = os.path.dirname(translated_file_path)

        save_path = os.path.join(save_dir, file_name)

        # 写入 EPUB 文件
        # 在写入前检查所有 EpubHtml 项目，避免空文档导致 lxml.ParserError
        try:
            for html_item in list(book.get_items_of_type(epub.EpubHtml)):
                try:
                    body = html_item.get_body_content()
                except Exception:
                    body = None
                if isinstance(body, bytes):
                    try:
                        body_str = body.decode('utf-8', errors='ignore').strip()
                    except Exception:
                        body_str = ''
                elif isinstance(body, str):
                    body_str = body.strip()
                else:
                    body_str = ''
                if not body_str:
                    print(f"警告: EpubHtml 内容为空，file_name={getattr(html_item,'file_name',None)!r}, title={getattr(html_item,'title',None)!r}，将替换为占位符。")
                    html_item.content = '<p></p>'
        except Exception as e:
            print(f"警告: 检查 EpubHtml 内容时出错: {e}")

        # 额外检查：遍历所有项目，确保任何可返回 body 的项都不为空（防止 ebooklib/lxml 报错）
        try:
            for item in list(book.get_items()):
                if hasattr(item, 'get_body_content'):
                    try:
                        body = item.get_body_content()
                    except Exception:
                        body = None
                    if isinstance(body, bytes):
                        try:
                            body_str = body.decode('utf-8', errors='ignore').strip()
                        except Exception:
                            body_str = ''
                    elif isinstance(body, str):
                        body_str = body.strip()
                    else:
                        body_str = ''

                    if not body_str:
                        print(f"警告: 发现空内容项，类型={type(item).__name__}, file_name={getattr(item,'file_name',None)!r}, title={getattr(item,'title',None)!r}，将尝试替换为占位符。")
                        if hasattr(item, 'content'):
                            try:
                                item.content = '<p></p>'
                            except Exception as e:
                                print(f"警告: 无法设置占位符 content: {e}")
        except Exception as e:
            print(f"警告: 遍历 EPUB 项目时出错: {e}")

        epub.write_epub(save_path, book, {})

        print(f"DEBUG: EPUB saved to {save_path}")

        return save_path

    def epub_format(self, epub_file_path, destination_file=None, toc_file=None, state='f_trans_unfinished', make_txt=False):
        """
        从 EPUB 文件生成与 lnrj_format 相同结构的 JSON（TranslateFile.json）。
        参数:
            epub_file_path (str): 源 epub 文件路径
            destination_file (str|None): 输出 JSON 路径，默认使用项目路径下的 TranslateFile.json 或 epub 同目录
            toc_file (str|None): 外部目录 JSON 文件（包含 "chapters" 列表），若提供优先使用
            state (str): 每个段落的状态字段，默认 'f_trans_unfinished'
            make_txt (bool): 是否额外输出纯文本 txt（按提取顺序拼接），默认 False
        返回:
            str: 写入的 JSON 文件路径
        """
        try:
            from ebooklib import epub
        except ImportError:
            raise ImportError("请先安装 ebooklib: pip install ebooklib")
        import re

        if not epub_file_path or not os.path.exists(epub_file_path):
            raise FileNotFoundError(f"EPUB 文件未找到: {epub_file_path}")

        # 读取 epub
        book = epub.read_epub(epub_file_path)

        # 尝试获取标题与描述
        title = None
        try:
            # ebooklib metadata 返回格式可能为 list of tuples
            md_title = book.get_metadata('DC', 'title')
            if md_title:
                title = md_title[0][0]
        except Exception:
            title = None
        if not title:
            title = os.path.splitext(os.path.basename(epub_file_path))[0]

        description = ''
        try:
            md_desc = book.get_metadata('DC', 'description')
            if md_desc:
                description = md_desc[0][0]
        except Exception:
            description = ''

        # 优先使用外部 toc_file（若存在）
        toc_titles = []
        default_toc = os.path.join(self.project_path, "sourcefile", "table_of_content.json") if self.project_path else None
        toc_file = toc_file if toc_file else default_toc
        if toc_file and os.path.exists(toc_file):
            try:
                print(f"DEBUG: 使用外部目录文件: {toc_file}")
                with open(toc_file, 'r', encoding='utf-8') as f:
                    toc_data = json.load(f)
                    toc_titles = [t for t in toc_data.get('chapters', []) if isinstance(t, str)]
                print(f"DEBUG: 从外部目录文件提取到 {len(toc_titles)} 个标题: {toc_titles[:5]}")
            except Exception as ex:
                print(f"DEBUG: 读取外部目录文件失败: {ex}")
                toc_titles = []

        # 如果外部 toc 为空，则尝试从 epub 的 toc 中提取标题
        def _extract_titles_from_epub_toc(toc_list, out):
            # toc_list 可能是 nested list/tuple 或 Link/Section 对象
            for item in toc_list:
                if isinstance(item, (list, tuple)):
                    # 链表或 (Link, subitems)
                    for sub in item:
                        # 递归调用即可
                        if isinstance(sub, (list, tuple)):
                            _extract_titles_from_epub_toc(sub, out)
                        else:
                            t = getattr(sub, 'title', None)
                            if t:
                                out.append(t)
                else:
                    t = getattr(item, 'title', None)
                    if t:
                        out.append(t)
                    # 递归子项
                    children = getattr(item, 'children', None)
                    if children:
                        _extract_titles_from_epub_toc(children, out)

        if not toc_titles:
            try:
                epub_toc = book.toc
                if epub_toc:
                    _extract_titles_from_epub_toc(epub_toc, toc_titles)
                    print(f"DEBUG: 从 epub.toc 提取到 {len(toc_titles)} 个标题: {toc_titles[:5]}")
            except Exception:
                toc_titles = toc_titles

        # 辅助：从 html 内容提取段落 (以 <p> 或 <h1>-<h6> 为主)
        def _extract_paragraphs_from_html(html_str):
            # 更鲁棒的段落提取：移除 script/style，处理 <br>，移除 ruby 注音（<rt>）并展开 <ruby>，
            # 优先寻找 class="main" 容器，然后按常见块级元素提取文本，最后做空白归一化与噪音过滤。
            from bs4 import BeautifulSoup
            import re
            if not html_str:
                return []
            soup = BeautifulSoup(html_str, 'lxml')
            # 移除不可见或无关内容
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            # 移除 ruby 注音的 rt 元素，展开 ruby 保留基文本
            for rt in soup.find_all('rt'):
                try:
                    rt.decompose()
                except Exception:
                    pass
            for ruby in soup.find_all('ruby'):
                try:
                    ruby.unwrap()
                except Exception:
                    # 若无法 unwrap，尝试移除但保留内容
                    try:
                        ruby.replace_with(ruby.get_text())
                    except Exception:
                        ruby.decompose()
            # 将 <br> 替换为换行，便于后续按空行切分
            for br in soup.find_all('br'):
                br.replace_with('\n')

            parts = []
            # 优先在具有 main 类的容器中搜寻
            main_containers = soup.find_all(class_='main')
            search_roots = main_containers if main_containers else ([soup.body] if soup.body else [soup])

            for root in search_roots:
                if not root:
                    continue
                for tag in root.find_all(['p', 'div', 'section', 'article', 'blockquote',
                                           'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                    # 使用 separator='' 避免内联元素之间生成多余空格
                    text = tag.get_text(separator='', strip=True)
                    if text:
                        # 标记这是来自标题标签（h1-h6）的内容，便于外层判断
                        is_title = tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                        parts.append({'text': text, 'is_title': is_title})

            # 回退：如果仍然没有内容，则按整个文档的纯文本按空行切分
            if not parts:
                print("DEBUG: No parts found, using fallback")
                text_only = soup.get_text('\n')
                snippet = text_only[:200].replace('\n', '\\n')
                print(f"DEBUG: text_only length: {len(text_only)}, snippet: {snippet}")
                raw_parts = re.split(r'\n\s*\n', text_only)
                for p in raw_parts:
                    t = re.sub(r'\s+', ' ', p).strip()
                    if t:
                        parts.append({'text': t, 'tag': None, 'is_title': False})

            # 归一化并过滤掉噪音段（如仅含 SVG 占位符或空行）
            cleaned = []
            for item in parts:
                p = item['text']
                p2 = p.replace('\r', '').replace('\xa0', ' ').strip()
                p2 = re.sub(r'\s+', ' ', p2)
                # 忽略过短或不含字母/数字/汉字的段落
                if len(p2) < 2:
                    continue
                if not re.search(r'[\w\u4e00-\u9fff]', p2):
                    continue
                cleaned.append({'text': p2, 'is_title': item.get('is_title', False)})
            return cleaned

        # 遍历 epub 的文本 HTML 项，根据 spine 顺序提取文本段落
        html_items = []
        try:
            for item in book.get_items_of_type(epub.EpubHtml):
                # 跳过导航、空文档等
                fn = getattr(item, 'file_name', '')
                # 只收集正文类型的 html
                html_items.append((fn, item))
        except Exception:
            html_items = []
        # 回退：有些 EPUB 的文档未被识别为 epub.EpubHtml（ebooklib 版本差异或特殊打包方式）
        if not html_items:
            print("DEBUG: epub.EpubHtml 未返回项，尝试回退遍历所有项目以查找可读内容")
            try:
                all_items = list(book.get_items())
                print(f"DEBUG: book.get_items() 总项数: {len(all_items)}; 前10 类型样例: {[type(it).__name__ for it in all_items[:10]]}")
                for item in all_items:
                    fn = getattr(item, 'file_name', None) or getattr(item, 'href', None) or None
                    # 尝试读取内容
                    content = None
                    try:
                        if hasattr(item, 'get_body_content'):
                            content = item.get_body_content()
                        elif hasattr(item, 'get_content'):
                            content = item.get_content()
                    except Exception:
                        content = None
                    if isinstance(content, bytes):
                        try:
                            content = content.decode('utf-8', errors='ignore')
                        except Exception:
                            content = None
                    if content and isinstance(content, str) and content.strip():
                        html_items.append((fn or '', item))
                # print(f"DEBUG: 回退后收集到 html_items: {len(html_items)}; 前5: {[fn for fn, _ in html_items[:5]]}")
            except Exception as ex:
                print(f"DEBUG: 回退遍历 book.get_items() 时出错: {ex}")
        print(f"DEBUG: 收集到 html_items: {len(html_items)}")
        # if html_items:
        #     # print("DEBUG: 前5 html 文件名:", [fn for fn, _ in html_items[:5]])

        # 为了保持顺序，使用 spine 中的 href 顺序，如果 spine 可用则映射
        spine_hrefs = []
        try:
            for sp in book.spine:
                # spine 中可能包含 'nav' 或 (idref, linear)
                if isinstance(sp, tuple) and len(sp) >= 1:
                    spine_hrefs.append(sp[0])
                elif isinstance(sp, str):
                    spine_hrefs.append(sp)
        except Exception:
            spine_hrefs = []
        # print(f"DEBUG: spine_hrefs count: {len(spine_hrefs)}; sample: {spine_hrefs[:10]}")

        # 创建 file_name -> item 映射
        fn_map = {fn: item for fn, item in html_items}

        ordered_items = []
        if spine_hrefs:
            for href in spine_hrefs:
                # spine 中的 href 可能是 idref，对应到 item.get_id() 或 file_name
                # 先尝试匹配 file_name
                if href in fn_map:
                    ordered_items.append(fn_map[href])
                    continue
                # 再尝试通过 id
                for fn, itm in html_items:
                    if getattr(itm, 'id', None) == href or getattr(itm, 'file_name', None) == href:
                        ordered_items.append(itm)
                        break
            # 若仍为空，则退回到 html_items 顺序
            if not ordered_items:
                ordered_items = [item for _, item in html_items]
        else:
            ordered_items = [item for _, item in html_items]
        # print(f"DEBUG: ordered_items count: {len(ordered_items)}")

        # 生成章节列表
        chapters = []
        cid = 1
        # 将 toc_titles 预处理为去除前后空白并作为集合用于匹配
        toc_set = {t.strip() for t in toc_titles if isinstance(t, str)}

        # 新增：在遇到第一个标题之前，收集文本作为 description
        pre_title_description_parts = []
        found_first_title = False

        for item in ordered_items:
            try:
                fn = getattr(item, 'file_name', None)
                # print(f"DEBUG: processing item file_name={fn}, id={getattr(item,'id',None)}")
                raw = None
                try:
                    raw = item.get_body_content()
                except Exception:
                    try:
                        raw = item.get_content()
                    except Exception:
                        raw = None
                if isinstance(raw, bytes):
                    try:
                        raw = raw.decode('utf-8', errors='ignore')
                    except Exception:
                        raw = raw.decode('utf-8', errors='ignore')
                if not raw:
                    print(f"DEBUG: item {fn} 内容为空或无法读取")
                    continue
                html_str = raw if isinstance(raw, str) else str(raw)
                snippet = html_str[:200].replace('\n', '\\n')
                # print(f"DEBUG: html_str snippet for {fn}: {snippet}")
                paras = _extract_paragraphs_from_html(html_str)
                paras_sample = paras[0]['text'][:200] if paras else ''
                # print(f"DEBUG: extracted {len(paras)} paragraphs from {fn}; sample: {paras_sample}")
                for p_item in paras:
                    t = p_item.get('text', '').strip()
                    is_heading_tag = p_item.get('is_title', False)
                    if not t:
                        continue
                    # 判断是否为目录标题（来自 h1-h6 或在外部 toc 中匹配）
                    starts_with_toc = any(t.startswith(tt) for tt in toc_set) if toc_set else False
                    in_toc = t in toc_set if toc_set else False
                    typ = 'title_lv1' if (is_heading_tag or in_toc or starts_with_toc) else 'main_text'

                    # 在遇到第一个标题之前，将非标题文本视为 description 内容
                    if not found_first_title and typ != 'title_lv1':
                        pre_title_description_parts.append(t)
                        continue
                    if not found_first_title and typ == 'title_lv1':
                        found_first_title = True

                    chapters.append({
                        'id': cid,
                        'original-text': t,
                        'translation-text': '',
                        'type': typ,
                        'state': state
                    })
                    cid += 1
            except Exception as e:
                print(f"DEBUG: 处理 item 时出错: {e}")
                continue

        # 如果没有章节则报错
        if not chapters:
            raise ValueError('未从 EPUB 中提取到章节内容')

        # 将 metadata description 与 pre_title_description_parts 组合，若 metadata 为空则优先使用前置文本
        if pre_title_description_parts:
            pre_desc = '\n'.join(pre_title_description_parts).strip()
            if description:
                # 若已有描述，则合并并去重
                if pre_desc not in description:
                    description = (description + '\n' + pre_desc).strip()
            else:
                description = pre_desc

        output_json = {
            'title': title,
            'description': description,
            'chapters': chapters
        }

        # 确定保存路径
        if destination_file:
            save_path = destination_file
        else:
            if self.project_path:
                save_path = os.path.join(self.project_path, 'TranslateFile.json')
            else:
                save_path = os.path.splitext(epub_file_path)[0] + '_TranslateFile.json'

        print(f"DEBUG: 写入 JSON 文件到: {save_path}")
        # 写入文件（不包含图片或资源结构）
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, ensure_ascii=False, indent=2)

        # 可选：额外输出 txt
        if make_txt:
            try:
                # 保存目录：优先放到对应 _project/sourcefile 下
                if self.project_path:
                    txt_dir = os.path.join(self.project_path, 'sourcefile')
                    os.makedirs(txt_dir, exist_ok=True)
                else:
                    txt_dir = os.path.dirname(epub_file_path)

                # 文件名：与源 epub 同名（仅扩展名改为 .txt）
                src_base = os.path.splitext(os.path.basename(epub_file_path))[0]
                txt_path = os.path.join(txt_dir, src_base + '.txt')

                # 只输出章节内容，标题/正文都包含；并在每段/每句后额外空一行
                blocks = []
                if title and str(title).strip():
                    blocks.append(str(title).strip())
                if description and str(description).strip():
                    blocks.append(str(description).strip())

                for c in chapters:
                    t = c.get('original-text', '')
                    if not t:
                        continue
                    blocks.append(str(t).strip())

                # block 之间用两个换行分隔（保证每句/每段后都额外空一行）
                content = ('\n\n'.join([b for b in blocks if b]))
                # 末尾也补齐一个空行（两个换行）
                content = content.rstrip() + '\n\n'

                with open(txt_path, 'w', encoding='utf-8') as tf:
                    tf.write(content)
                print(f"DEBUG: 写入 TXT 文件到: {txt_path}")
            except Exception as ex:
                print(f"警告: 输出 txt 失败: {ex}")

        return save_path
    
if __name__ == "__main__":
    # 简单测试
    project_path = "D:\\Gumiho_demo\\backend\\超时空辉耀姬_project"
    disposer = EpubDispose(project_path)
    epub_path = "D:\\Gumiho_demo\\backend\\超时空辉耀姬_project\\sourcefile\\超かぐや姫！.epub"
    # disposer.epub_format(epub_path, make_txt=True)
    # output_json = disposer.epub_format(epub_path)
    # print(f"Generated JSON: {output_json}")

    json_path = "D:\\Gumiho_demo\\backend\\超时空辉耀姬_project\\TranslateFile.json"
    # output_epub = disposer.normal_epub_rebuild(1, 10, translated_file_path=json_path)
    # print(f"Generated EPUB: {output_epub}")
    disposer.epub_refilled(epub_path, translated_file_path=json_path, novel_status="proofreading_finished", with_original_text_or_not=False)

