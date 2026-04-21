"""Data cleaning and preprocessing module for crawled news content."""
import re
import string
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CleanResult:
    """Result of data cleaning."""
    original: str
    cleaned: str
    is_valid: bool
    issues: List[str]
    statistics: Dict


class DataCleaner:
    """Data cleaner for Chinese text content."""

    def __init__(self):
        self.min_length = 10
        self.max_length = 500
        self.invalid_patterns = [
            r"^[\d\s\.,，。、；：""''「」【】（）()\-\_\+\=\*\/]+$",
            r"^[a-zA-Z\s\d]+$",
            r"http[s]?://",
            r"www\.",
            r"\.com|\.cn|\.net|\.org",
            r"点击|阅读|更多|查看|下载",
            r"来源[:：]|作者[:：]|编辑[:：]|责编[:：]",
            r"本文来自|原标题|责任编辑",
            r"上一篇|下一篇|相关阅读",
            r"分享到|微信|微博|QQ",
            r"收藏|打印|举报",
            r"未经授权|不得转载|版权所有",
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.invalid_patterns]

    def clean(self, text: str) -> CleanResult:
        """Clean a single text string."""
        original = text
        issues = []
        statistics = {
            "original_length": len(text),
            "cleaned_length": 0,
            "removed_chars": 0,
            "removed_spaces": 0,
            "removed_special": 0,
        }

        cleaned = text

        cleaned = self._normalize_whitespace(cleaned)
        statistics["removed_spaces"] = len(original) - len(cleaned)

        cleaned = self._remove_html_tags(cleaned)

        cleaned = self._normalize_punctuation(cleaned)

        cleaned = self._remove_control_chars(cleaned)
        statistics["removed_special"] = len(original) - len(cleaned) - statistics["removed_spaces"]

        cleaned = cleaned.strip()

        statistics["cleaned_length"] = len(cleaned)
        statistics["removed_chars"] = len(original) - len(cleaned)

        is_valid, validation_issues = self._validate(cleaned)
        issues.extend(validation_issues)

        return CleanResult(
            original=original,
            cleaned=cleaned,
            is_valid=is_valid,
            issues=issues,
            statistics=statistics,
        )

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters."""
        text = re.sub(r"[\r\n\t\f\v]+", " ", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        text = re.sub(r"[\u3000]+", " ", text)
        return text

    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags and entities."""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"&[a-zA-Z]+;", "", text)
        text = re.sub(r"&#\d+;", "", text)
        return text

    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation to Chinese style."""
        punctuation_map = {
            ",": "，",
            ".": "。",
            "!": "！",
            "?": "？",
            ":": "：",
            ";": "；",
            "(": "（",
            ")": "）",
            "[": "【",
            "]": "】",
            "{": "「",
            "}": "」",
            '"': "“",
            "'": "‘",
        }

        for eng, chn in punctuation_map.items():
            text = text.replace(eng, chn)

        text = re.sub(r"[。！？]{2,}", "。", text)
        text = re.sub(r"[，,]{2,}", "，", text)

        return text

    def _remove_control_chars(self, text: str) -> str:
        """Remove control and special characters."""
        control_chars = "".join(
            [chr(char) for char in range(32) if char not in (9, 10, 13)]
        )
        text = text.translate(str.maketrans("", "", control_chars))
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
        return text

    def _validate(self, text: str) -> Tuple[bool, List[str]]:
        """Validate cleaned text."""
        issues = []

        if len(text) < self.min_length:
            issues.append(f"Text too short: {len(text)} chars (min: {self.min_length})")
            return False, issues

        if len(text) > self.max_length:
            issues.append(f"Text too long: {len(text)} chars (max: {self.max_length})")

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        if chinese_chars < 5:
            issues.append("Too few Chinese characters")
            return False, issues

        for pattern in self.compiled_patterns:
            if pattern.search(text):
                issues.append(f"Matches invalid pattern: {pattern.pattern[:50]}...")
                return False, issues

        if text.isdigit():
            issues.append("Text contains only digits")
            return False, issues

        if all(char in string.punctuation or char.isspace() for char in text):
            issues.append("Text contains only punctuation and spaces")
            return False, issues

        return len(issues) == 0, issues

    def clean_batch(self, texts: List[Dict], content_key: str = "content") -> List[Dict]:
        """Clean a batch of text dictionaries."""
        results = []

        for item in texts:
            text = item.get(content_key, "")
            clean_result = self.clean(text)

            item["cleaned"] = clean_result.cleaned
            item["is_valid"] = clean_result.is_valid
            item["cleaning_issues"] = clean_result.issues
            item["cleaning_stats"] = clean_result.statistics

            results.append(item)

        return results

    def filter_valid(self, cleaned_items: List[Dict]) -> List[Dict]:
        """Filter only valid cleaned items."""
        return [item for item in cleaned_items if item.get("is_valid", False)]

    def deduplicate(self, items: List[Dict], content_key: str = "cleaned") -> List[Dict]:
        """Remove duplicate items based on content."""
        seen = set()
        unique_items = []

        for item in items:
            content = item.get(content_key, "")
            if content and content not in seen:
                seen.add(content)
                unique_items.append(item)

        return unique_items


class TextClassifier:
    """Simple text classifier for categorizing news content."""

    def __init__(self):
        self.category_keywords = {
            "政治": ["政策", "政府", "会议", "领导", "调研", "视察", "部署", "落实", "改革", "发展", "党委", "党组", "书记", "市长", "省长"],
            "经济": ["经济", "企业", "投资", "金融", "市场", "产业", "贸易", "消费", "增长", "发展", "GDP", "税收", "财政", "银行", "证券"],
            "文化": ["文化", "艺术", "展览", "演出", "文学", "电影", "音乐", "舞蹈", "美术", "文物", "非遗", "传承", "旅游", "景区"],
            "教育": ["教育", "学校", "学生", "教师", "教学", "考试", "招生", "课程", "校园", "大学", "中学", "小学", "幼儿园"],
            "科技": ["科技", "创新", "研发", "技术", "专利", "发明", "人工智能", "大数据", "云计算", "互联网", "数字", "智能"],
            "医疗": ["医疗", "医院", "医生", "患者", "药品", "健康", "疫情", "防控", "疫苗", "卫生", "医保", "中医", "西医"],
            "环保": ["环保", "环境", "生态", "污染", "治理", "绿色", "低碳", "节能", "减排", "绿化", "湿地", "自然", "保护"],
            "交通": ["交通", "公路", "铁路", "航空", "水运", "出行", "运输", "物流", "车站", "机场", "港口", "地铁", "公交"],
            "安全": ["安全", "事故", "灾害", "救援", "应急", "消防", "治安", "犯罪", "诈骗", "盗窃", "危险", "隐患"],
            "社会": ["社会", "民生", "服务", "社区", "群众", "基层", "就业", "社保", "养老", "医疗", "教育", "住房", "扶贫"],
            "体育": ["体育", "运动", "比赛", "赛事", "运动员", "教练", "金牌", "亚军", "季军", "奥运会", "世界杯", "锦标赛"],
            "娱乐": ["娱乐", "明星", "电影", "电视", "综艺", "音乐", "歌手", "演员", "导演", "票房", "收视率", "颁奖"],
        }

    def classify(self, text: str) -> Tuple[str, float]:
        """Classify text into a category."""
        scores = {}

        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                count = text.count(keyword)
                if count > 0:
                    score += count * (1 if len(keyword) > 1 else 0.5)
            if score > 0:
                scores[category] = score

        if not scores:
            return "其他", 0.0

        best_category = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[best_category] / total_score if total_score > 0 else 0.0

        return best_category, confidence

    def classify_batch(self, items: List[Dict], content_key: str = "cleaned") -> List[Dict]:
        """Classify a batch of items."""
        for item in items:
            content = item.get(content_key, "")
            category, confidence = self.classify(content)
            item["classified_category"] = category
            item["classification_confidence"] = confidence

        return items


def clean_and_classify(sentences: List[Dict]) -> Dict:
    """Complete pipeline: clean and classify sentences."""
    cleaner = DataCleaner()
    classifier = TextClassifier()

    cleaned = cleaner.clean_batch(sentences)
    valid = cleaner.filter_valid(cleaned)
    unique = cleaner.deduplicate(valid)
    classified = classifier.classify_batch(unique)

    stats = {
        "total_input": len(sentences),
        "after_cleaning": len(cleaned),
        "valid_count": len(valid),
        "unique_count": len(unique),
        "classified_count": len(classified),
        "categories": {},
    }

    for item in classified:
        cat = item.get("classified_category", "其他")
        stats["categories"][cat] = stats["categories"].get(cat, 0) + 1

    return {
        "items": classified,
        "statistics": stats,
    }


if __name__ == "__main__":
    test_sentences = [
        {"content": "自治区党委召开会议，部署今年经济工作重点任务。"},
        {"content": "新疆日报社今天举办了一场精彩的文化艺术展览。"},
        {"content": "教育部门发布新规，加强学生体质健康管理。"},
        {"content": "点击阅读更多精彩内容..."}
    ]

    result = clean_and_classify(test_sentences)

    print("Cleaning and Classification Results:")
    print(f"Total: {result['statistics']['total_input']}")
    print(f"Valid: {result['statistics']['valid_count']}")
    print(f"Unique: {result['statistics']['unique_count']}")
    print(f"Categories: {result['statistics']['categories']}")

    for item in result["items"]:
        print(f"\nContent: {item['cleaned'][:50]}...")
        print(f"Category: {item['classified_category']} ({item['classification_confidence']:.2f})")
