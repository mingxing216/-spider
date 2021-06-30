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

    # 标题
    def get_paper_title(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title_text = selector.xpath("string(//h1/span)").extract_first()
            title = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", title_text)).strip()

        except Exception:
            title = ""

        return title

    # 作者单位
    def get_author_affiliation(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            affiliation_list = selector.xpath(
                "//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/text()".format(para)).extract()
            affiliation = '|'.join(affiliation_list).strip()

        except Exception:
            affiliation = ""

        return affiliation

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
