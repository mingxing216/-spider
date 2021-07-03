# -*-coding:utf-8-*-

import ast
import json
import re
import hashlib
import langid
from scrapy import Selector
from bs4 import BeautifulSoup

from Utils import timers
from Utils.captcha import RecognizeCode
from Utils.verfication_code import VerificationCode


class DomResultHolder(object):
    def __init__(self):
        self.dict = {}
        self.text = None

    def get(self, mode, text):
        if text != self.text:
            self.dict.clear()
            self.text = text

        if mode in self.dict:
            return self.dict[mode]

        if mode == 'Selector':
            self.dict[mode] = Selector(text=text)
            return self.dict[mode]

        if mode == 'BeautifulSoup':
            self.dict[mode] = BeautifulSoup(text, 'html.parser')
            return self.dict[mode]

        raise NotImplementedError


class Server(object):
    def __init__(self, logging):
        self.logger = logging
        self.dom_holder = DomResultHolder()

    # ---------------------
    # task script
    # ---------------------

    # 数据类型转换
    @staticmethod
    def get_eval_response(task_data):
        return ast.literal_eval(task_data)

    # 获取期刊列表页总页数
    def get_journal_total_page(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            span = selector.xpath("//span[@class='pagination-pages-label']/text()").extract()
            total_page = span[-1]

        except Exception:
            return 1

        return total_page

    # 获取期刊详情种子及附加信息
    def get_journal_list(self, text):
        journal_data_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            a_list = selector.xpath("//a[@class='anchor js-publication-title']/@href").extract()
            for a in a_list:
                journal_dict = {}
                journal_dict['url'] = 'https://www.sciencedirect.com' + a
                journal_dict['id'] = a.split('/')[-1]
                journal_data_list.append(journal_dict)

        except Exception:
            return journal_data_list

        return journal_data_list

    # 获取期刊论文列表页
    def get_issues_catalog(self, text):
        issues_catalog_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            issues_text = selector.xpath("//script[@type='application/json']/text()").extract_first()
            issues_json = json.loads(json.loads(issues_text))
            issn = issues_json.get('titleMetadata').get('issn')
            result_list = issues_json.get('issuesArchive').get('data').get('results')
            if issn:
                for result in result_list:
                    year = result.get('year')
                    if year:
                        issues_catalog_url = 'https://www.sciencedirect.com/journal/{}/year/{}/issues'.format(issn, year)
                        issues_catalog_list.append((issues_catalog_url, year))

        except Exception:
            return issues_catalog_list

        return issues_catalog_list

    # 获取论文详情及全文种子
    def get_paper_list(self, text, task):
        paper_data_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            li_list = selector.xpath("//ol[contains(@class, 'js-article-list')]/li")
            for li in li_list:
                if li.xpath("./h2"):
                    journal_column = li.xpath("./h2/text()").extract_first()
                else:
                    journal_column = ''

                dl_list = li.xpath(".//dl")
                for dl in dl_list:
                    paper_dict = {}
                    if dl.xpath("./dt/h3/a"):
                        paper_dict['url'] = 'https://www.sciencedirect.com' + dl.xpath("./dt/h3/a/@href").extract_first()
                    else:
                        continue
                    if dl.xpath("./dd/a[span[contains(text(), 'Download')]]"):
                        paper_dict['pdfUrl'] = 'https://www.sciencedirect.com' + dl.xpath("./dd/a[span[contains(text(), 'Download')]]/@href").extract_first()
                    else:
                        paper_dict['pdfUrl'] = ''

                    if dl.xpath("./dd[contains(@class, 'article-info')]/span[contains(@class, 'js-article-subtype')]"):
                        paper_dict['type'] = dl.xpath("./dd[contains(@class, 'article-info')]/span[contains(@class, 'js-article-subtype')]/text()").extract_first()
                    else:
                        paper_dict['type'] = ''

                    if dl.xpath("./dd[contains(@class, 'article-info')]/span[contains(@class, 'js-open-access')]"):
                        paper_dict['rights'] = dl.xpath("./dd[contains(@class, 'article-info')]/span[contains(@class, 'js-open-access')]/text()").extract_first()
                    else:
                        paper_dict['rights'] = ''

                    paper_dict['journalColumn'] = journal_column
                    paper_dict['journalUrl'] = task.get('journalUrl', '')
                    paper_dict['journalId'] = task.get('journalId', '')
                    paper_dict['year'] = task.get('year', '')
                    paper_dict['vol'] = task.get('vol', '')
                    paper_dict['issue'] = task.get('issue', '')
                    paper_data_list.append(paper_dict)

        except Exception:
            return paper_data_list

        return paper_data_list

    # ---------------------
    # data script
    # ---------------------

    # ====== 期刊、论文、文档、人物实体
    # 是否包含中文（判断语种）
    def hasChinese(self, data):
        for ch in data:
            if '\u4e00' <= ch <= '\u9fa5':
                return True

        return False

    # 语种识别
    @staticmethod
    def get_lang(text):
        return langid.classify(text)[0]

    # =================== 期刊实体 ======================
    # 标题
    def get_journal_title(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title_text = selector.xpath("string(//h1)").extract_first()
            title = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", title_text)).strip()

        except Exception:
            title = ''

        return title

    # 图片
    def get_journal_cover(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            img = selector.xpath("//span[@class='anchor-text']/img/@src").extract_first()

        except Exception:
            img = ''

        return img

    # 影响因子
    def get_impact_factor(self, text):
        data_list = []
        data_dict = {}
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            if selector.xpath("//div[contains(@class, 'js-cite-score')]"):
                data_dict['cite_score'] = selector.xpath(
                    "//div[contains(@class, 'js-cite-score')]//span[contains(@class, 'text-l')]/text()").extract_first().strip()

            if selector.xpath("//div[contains(@class, 'js-impact-factor')]"):
                data_dict['impact_factor'] = selector.xpath(
                    "//div[contains(@class, 'js-impact-factor')]//span[contains(@class, 'text-l')]/text()").extract_first().strip()
            else:
                return data_list

            data_list.append(data_dict)

        except Exception:
            return data_list

        return data_list

    # 图片
    def get_issn(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            issn = selector.xpath("//div[contains(@class, 'js-issn')]/text()").extract_first().strip()

        except Exception:
            issn = ''

        return issn

    # 权限
    def get_rights(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            rights_text = selector.xpath("string(//div[contains(@class, 'open-statement')])").extract_first()
            rights = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", rights_text)).strip()

        except Exception:
            rights = ''

        return rights

    # 摘要
    def get_abstract(self, text, url, downloader, s):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            if not selector.xpath("//div[h2[contains(@class, 'js-journal-info-heading')]]"):
                return

            if selector.xpath("//div[contains(@class, 'branded')]/a"):
                # 获取摘要所在页面
                abstract_url = url + '/about/aims-and-scope'
                abstract_resp = downloader.get_resp(url=abstract_url, method='GET', s=s)
                if abstract_resp is None:
                    self.logger.error('downloader | 摘要所在页响应失败, url: {}'.format(abstract_url))
                    return

                if not abstract_resp['data']:
                    self.logger.error('downloader | 摘要所在页响应失败, url: {}'.format(abstract_url))
                    return

                abstract_text = abstract_resp['data'].text
                selector = self.dom_holder.get(mode='Selector', text=abstract_text)
                abstract_html = selector.xpath("//div[contains(@class, 'js-aims-and-scope')]").extract_first()
            else:
                abstract_html = selector.xpath("//div[h2[contains(@class, 'js-journal-info-heading')]]/div/div").extract_first()

            abstract = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", abstract_html)).strip()

        except Exception:
            abstract = ''

        return abstract

    # 主编
    def get_chief_editor(self, url, downloader, s):
        # 获取主编
        editorial_url = url + '/about/editorial-board'
        editorial_resp = downloader.get_resp(url=editorial_url, method='GET', s=s)
        if editorial_resp is None:
            self.logger.error('downloader | 主编所在页响应失败, url: {}'.format(editorial_url))
            return ''

        if not editorial_resp['data']:
            self.logger.error('downloader | 主编所在页响应失败, url: {}'.format(editorial_url))
            return ''

        editorial_text = editorial_resp['data'].text
        selector = self.dom_holder.get(mode='Selector', text=editorial_text)
        try:
            if selector.xpath("//div[h3[contains(text(), 'in-Chief') or contains(text(), 'in-chief')]]"):
                chief_editor = ''.join(selector.xpath("//div[h3[contains(text(), 'in-Chief') or contains(text(), 'in-chief')]]/div").extract())
            else:
                chief_editor = ''

        except Exception:
            chief_editor = ''

        return chief_editor

    # 编辑
    def get_editors(self, url, downloader, s):
        # 获取主编
        editorial_url = url + '/about/editorial-board'
        editorial_resp = downloader.get_resp(url=editorial_url, method='GET', s=s)
        if editorial_resp is None:
            self.logger.error('downloader | 主编所在页响应失败, url: {}'.format(editorial_url))
            return ''

        if not editorial_resp['data']:
            self.logger.error('downloader | 主编所在页响应失败, url: {}'.format(editorial_url))
            return ''

        editorial_text = editorial_resp['data'].text
        selector = self.dom_holder.get(mode='Selector', text=editorial_text)
        try:
            if selector.xpath("//div[contains(@class, 'u-margin-xl-top')]"):
                editors = selector.xpath("//div[contains(@class, 'u-margin-xl-top')]").extract_first()
            else:
                editors = ''

        except Exception:
            editors = ''

        return editors

    # 期刊荣誉
    def get_honors(self, url, downloader, s):
        # 获取荣誉
        honors_url = url + '/about/abstracting-and-indexing'
        honors_resp = downloader.get_resp(url=honors_url, method='GET', s=s)
        if honors_resp is None:
            self.logger.error('downloader | 期刊荣誉所在页响应失败, url: {}'.format(honors_url))
            return ''

        if not honors_resp['data']:
            self.logger.error('downloader | 期刊荣誉所在页响应失败, url: {}'.format(honors_url))
            return ''

        honors_text = honors_resp['data'].text
        selector = self.dom_holder.get(mode='Selector', text=honors_text)
        try:
            if selector.xpath("//div[contains(@class, 'abstracting-and-indexing')]"):
                honors = selector.xpath("//div[contains(@class, 'abstracting-and-indexing')]").extract_first()
            else:
                honors = ''

        except Exception:
            honors = ''

        return honors

    # =============== 论文实体 ====================
    # 标题
    def get_paper_title(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title_text = selector.xpath("string(//h1/span)").extract_first()
            title = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", title_text)).strip()

        except Exception:
            title = ""

        return title

    # 作者
    def get_author(self, text):
        author_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            a_list = selector.xpath("//div[@class='author-group']/a")
            if a_list:
                for a in a_list:
                    span_list = a.xpath("./span/span[contains(@class, 'text')]/text()").extract()
                    span_text = ' '.join(span_list)
                    author_list.append(span_text)

                author = '|'.join(author_list)
            else:
                author = ''

        except Exception:
            author = ''

        return author

    # 作者单位
    def get_affiliation(self, text):
        author_affiliation_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            content = selector.xpath("//script[@type='application/json']/text()").extract_first()
            content_dict = json.loads(content)
            author_info_list = content_dict['authors']['content'][0]['$$']
            if author_info_list:
                for author_info in author_info_list:
                    if author_info['#name'] == 'affiliation':
                        affiliation_list = author_info['$$']
                        for affiliation in affiliation_list:
                            if affiliation['#name'] == 'textfn':
                                author_affiliation_list.append(affiliation['_'])

                author_affiliation = '|'.join(author_affiliation_list)
            else:
                author_affiliation = ''

        except Exception:
            author_affiliation = ''

        return author_affiliation

    # doi
    def get_doi(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            doi_url = selector.xpath("//a[@class='doi']/@href").extract_first()

        except Exception:
            doi_url = ''

        return doi_url

    # 摘要
    def get_paper_abstract(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            abstract_list = selector.xpath("//div[h2[text()='Abstract']]/div").extract()
            abstract = ''.join(abstract_list)

        except Exception:
            abstract = ''

        return abstract

    # 关键词
    def get_paper_keyword(self, text):
        keyword_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            div_list = selector.xpath("//div[h2[text()='Keywords']]/div")
            for div in div_list:
                text = div.xpath("string(.)").extract_first()
                kw = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", text)).strip()
                keyword_list.append(kw)

            keyword = '|'.join(keyword_list)

        except Exception:
            keyword = ''

        return keyword

    # 期刊名称
    def get_journal_name(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            journal_name = selector.xpath("//h2[contains(@class, 'publication-title')]//text()").extract_first().strip()

        except Exception:
            journal_name = ''

        return journal_name

    # 年卷期起止页
    def get_journal_info(self, text):
        journal_dict = {}
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            journal_info = selector.xpath("string(//div[@class='text-xs'])").extract_first()
            journal_list = journal_info.split(',')
            for journal in journal_list:
                if 'Volume' in journal:
                    journal_dict['vol'] = re.findall(r"Volume(.*)", journal)[0].strip()
                if 'Issue' in journal:
                    journal_dict['issue'] = re.findall(r"Issue(.*)", journal)[0].strip()
                if re.findall(r"\s+\d{4}$", journal):
                    journal_dict['date'] = journal.strip()
                    journal_dict['year'] = re.findall(r"\d{4}", journal)[0].strip()
                if 'Page' in journal:
                    journal_dict['pages'] = re.findall(r"Pages?(.*)", journal)[0].strip()

        except Exception:
            return journal_dict

        return journal_dict

    # 参考文献
    def get_refer(self, text, url, id, downloader, s):
        reference_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            content = selector.xpath("//script[@type='application/json']/text()").extract_first()
            content_dict = json.loads(content)
            token = content_dict['article']['entitledToken']
            if token:
                refer_url = url.format(id, token)
                refer_resp = downloader.get_resp(url=refer_url, method='GET', s=s)
                if refer_resp is None:
                    self.logger.error('downloader | 参考文献json页响应失败, url: {}'.format(refer_url))
                    return reference_list
                if refer_resp['status'] == 404:
                    return reference_list
                if not refer_resp['data']:
                    self.logger.error('downloader | 参考文献json页响应失败, url: {}'.format(refer_url))
                    return reference_list

                refer_json = refer_resp['data'].json()

                refer_list = refer_json['content'][0]['$$']
                if refer_list:
                    for refer in refer_list:
                        if 'bibliography' in refer.get('#name', ''):
                            fir_list = refer.get('$$', '')
                            if fir_list:
                                for fir in fir_list:
                                    refer_dict = {}
                                    sec_list = fir.get('$$', '')
                                    if sec_list:
                                        for sec in sec_list:
                                            if 'reference' in sec.get('#name', ''):
                                                third_list = sec.get('$$', '')
                                                for third in third_list:
                                                    if 'contribution' in third.get('#name', ''):
                                                        cont_list = third.get('$$', '')
                                                        for contribute in cont_list:
                                                            if 'author' in contribute.get('#name', ''):
                                                                author_list = contribute.get('$$', '')
                                                                if author_list:
                                                                    authors = []
                                                                    for author in author_list:
                                                                        auth = []
                                                                        for au in author.get('$$', ''):
                                                                            auth.append(au.get('_', ''))
                                                                        authors.append(' '.join(auth))
                                                                    refer_dict['author'] = '|'.join(authors)

                                                            if 'title' in contribute.get('#name', ''):
                                                                refer_dict['title'] = contribute.get('$$', '')[0].get('_', '')

                                                    if 'host' in third.get('#name', ''):
                                                        host_list = third.get('$$', '')
                                                        for host in host_list:
                                                            if 'edited-book' in host.get('#name', ''):
                                                                edited_list = host.get('$$', '')
                                                                if edited_list:
                                                                    for edited in edited_list:
                                                                        if 'title' in edited.get('#name', ''):
                                                                            for series in edited.get('$$', ''):
                                                                                if 'title' in series.get('#name', ''):
                                                                                    refer_dict['journal_name'] = \
                                                                                    series.get('$$', '')[0].get('_', '')
                                                                                if 'volume' in series.get('#name', ''):
                                                                                    refer_dict['vol'] = series.get('_', '')
                                                                        if 'issue' in edited.get('#name', ''):
                                                                            refer_dict['issue'] = edited.get('_', '')
                                                                        if 'date' in edited.get('#name', ''):
                                                                            refer_dict['year'] = edited.get('_', '')
                                                                        if 'publisher' in edited.get('#name', ''):
                                                                            pub_list = []
                                                                            for pub in edited.get('$$', ''):
                                                                                pub_list.append(pub.get('_', ''))
                                                                            refer_dict['publisher'] = '|'.join(pub_list)

                                                            if 'issue' in host.get('#name', ''):
                                                                issue_list = host.get('$$', '')
                                                                if issue_list:
                                                                    for issue in issue_list:
                                                                        if 'series' in issue.get('#name', ''):
                                                                            for series in issue.get('$$', ''):
                                                                                if 'title' in series.get('#name', ''):
                                                                                    refer_dict['journal_name'] = series.get('$$', '')[0].get('_', '')
                                                                                if 'volume' in series.get('#name', ''):
                                                                                    refer_dict['vol'] = series.get('_', '')
                                                                        if 'issue' in issue.get('#name', ''):
                                                                            refer_dict['issue'] = issue.get('_', '')
                                                                        if 'date' in issue.get('#name', ''):
                                                                            refer_dict['year'] = issue.get('_', '')

                                                            if 'page' in host.get('#name', ''):
                                                                for page in host.get('$$', ''):
                                                                    if 'first-page' in page.get('#name', ''):
                                                                        refer_dict['start_page'] = page.get('_', '')
                                                                    if 'last-page' in page.get('#name', ''):
                                                                        refer_dict['end_page'] = page.get('_', '')

                                                            if 'article-number' in host.get('#name', ''):
                                                                refer_dict['article_number'] = host.get('_', '')

                                            if 'source-text' in sec.get('#name', ''):
                                                refer_dict['full_content'] = sec.get('_', '')

                                    reference_list.append(refer_dict)

        except Exception:
            return reference_list

        return reference_list

    # 引证文献
    def get_cited(self, url, id, downloader, s):
        cited_list = []
        cited_url = url.format(id)
        cited_resp = downloader.get_resp(url=cited_url, method='GET', s=s)
        if cited_resp is None:
            self.logger.error('downloader | 引证文献json页响应失败, url: {}'.format(cited_url))
            return cited_list
        if cited_resp['status'] == 404:
            return cited_list
        if not cited_resp['data']:
            self.logger.error('downloader | 引证文献json页响应失败, url: {}'.format(cited_url))
            return cited_list

        try:
            cited_json = cited_resp['data'].json()

            article_list = cited_json.get('articles', '')
            if article_list:
                for article in article_list:
                    cited_dict = {}
                    cited_dict['title'] = article.get('articleTitle', '')
                    cited_dict['author'] = article.get('authors', '').replace(',', '|')
                    cited_dict['doi'] = article.get('doi', '')
                    if article.get('pii', ''):
                        cited_dict['url'] = 'https://www.sciencedirect.com/science/article/abs/pii/' + article.get('pii', '')
                    else:
                        cited_dict['url'] = ''
                    pages = article.get('page', '')
                    if pages:
                        if '-' in pages:
                            page_list = pages.split('-')
                            cited_dict['start_page'] = page_list[0]
                            cited_dict['end_page'] = page_list[1]
                        else:
                            cited_dict['start_page'] = pages
                            cited_dict['end_page'] = ''
                    cited_dict['journal_name'] = article.get('publicationTitle', '')
                    cited_dict['year'] = article.get('publicationYear', '')
                    cited_dict['vol'] = re.findall(r"Volume(.*)", article.get('volume', ''), re.I)[0].strip()
                    cited_list.append(cited_dict)

        except Exception:
            return cited_list

        return cited_list

    # 目录
    def get_catalog(self, json_dict):
        catalog_list = []
        catalog_temp_list = []
        try:
            outline_list = json_dict.get('outline', '')
            if outline_list:
                for outline in outline_list:
                    info_list = outline.get('$$', '')
                    if info_list:
                        fir_info = []
                        extend_info = []
                        for info in info_list:
                            if info.get('#name', '') == 'label':
                                fir_num = info.get('_', '')
                                fir_info.append(fir_num)
                            if info.get('#name', '') == 'title':
                                fir_title = info.get('_', '')
                                fir_info.append(fir_title)

                            if info.get('#name', '') == 'entry':
                                entry_list = info.get('$$', '')
                                if entry_list:
                                    sec_info = []
                                    for entry in entry_list:
                                        if entry.get('#name', '') == 'label':
                                            sec_num = entry.get('_', '')
                                            sec_info.append(sec_num)
                                        if entry.get('#name', '') == 'title':
                                            if not entry.get('$$', ''):
                                                sec_title = entry.get('_', '')
                                                sec_info.append(sec_title)
                                            else:
                                                third_list = []
                                                for third in entry.get('$$', ''):
                                                    third_list.append(third.get('_', ''))
                                                sec_info.append(' '.join(third_list))

                                    extend_info.append(' '.join(sec_info))
                        catalog_temp_list.append(' '.join(fir_info))
                        catalog_temp_list.extend(extend_info)

                for cata in catalog_temp_list:
                    catalog_list.append('<li>{}</li>'.format(cata))
                catalog = '<ul>{}</ul>'.format(''.join(catalog_list))

            else:
                catalog = ''

        except Exception:
            catalog = ''

        return catalog

    # 组图图片
    def get_pic_url(self, json_dict, title):
        url_list = []
        try:
            attachments_list = json_dict.get('attachments', '')
            if attachments_list:
                for attachments in attachments_list:
                    if 'lrg.jpg' in attachments.get('attachment-eid', ''):
                        url_dict = {'url': 'https://ars.els-cdn.com/content/image/' + attachments.get('attachment-eid', ''),
                                    'size': attachments.get('filesize', ''),
                                    'title': title}
                        url_list.append(url_dict)

        except Exception:
            url_list = ''

        return url_list

    # =========== 文档实体 =============
    # 获取真正全文链接
    def get_real_pdf_url(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            real_pdf_url = selector.xpath("//div[@id='redirect-message']/p/a/@href").extract_first()

        except Exception:
            real_pdf_url = ''

        return real_pdf_url

    # 获取文档
    def get_media(self, media_data, media_key, ss, format='', size=''):
        label_obj = {}
        media_list = []
        try:
            if media_data:
                if media_data['url']:
                    media_obj = {
                        'url': media_data.get('url'),
                        'title': media_data.get('biz_title', ''),
                        'desc': '',
                        'sha': hashlib.sha1(media_data.get('url').encode('utf-8')).hexdigest(),
                        'ss': ss,
                        'format': format,
                        'size': size
                    }
                    media_list.append(media_obj)
                label_obj[media_key] = media_list
        except Exception:
            return label_obj

        return label_obj

    # 获取组图
    def get_pics(self, media_data, media_key, ss, format=''):
        label_obj = {}
        media_list = []
        try:
            if media_data:
                for media in media_data:
                    if media['url']:
                        media_obj = {
                            'url': media['url'],
                            'title': media.get('title', ''),
                            'desc': '',
                            'sha': hashlib.sha1(media['url'].encode('utf-8')).hexdigest(),
                            'ss': ss,
                            'format': format,
                            'size': media.get('size', '')
                        }
                        media_list.append(media_obj)
                label_obj[media_key] = media_list
        except Exception:
            return label_obj

        return label_obj

    # 文本格式全文
    def is_fulltext_page(self, resp):
        if len(resp.content) < 100 or '未找到全文' in resp.text:
            return False

        return True

    # 获取全文
    def get_fulltext(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            full_text = selector.xpath("//div[@id='search_nsfc']").extract_first()

        except Exception:
            full_text = ""

        return full_text

    # 关联关系
    def rela_entity(self, url, key, sha, ss):
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = ss
        except Exception:
            return e

        return e
