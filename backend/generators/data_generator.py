"""Dataset generators for different task types."""
import random
from faker import Faker

fake = Faker("zh_CN")
fake_en = Faker("en_US")


def generate_text_classification(count: int, labels: list[str], **kwargs) -> list[dict]:
    """Generate text classification samples."""
    if not labels:
        labels = ["正面", "负面", "中性"]

    topics = [
        "产品质量非常好，使用体验很棒！",
        "这个服务太差了，完全不值这个价钱。",
        "还行吧，一般般，没什么特别的。",
        "超级推荐，绝对值得购买，五星好评！",
        "非常失望，和描述完全不符合，要求退款。",
        "物流很快，包装完好，产品符合预期。",
        "客服态度不好，问题一直没解决。",
        "性价比很高，用了一段时间感觉不错。",
        "质量一般，做工粗糙，有点后悔买了。",
        "完全超出预期，太惊喜了，以后还会购买！",
    ]

    samples = []
    for i in range(count):
        text = random.choice(topics) if i < len(topics) else fake.sentence(nb_words=random.randint(10, 30))
        samples.append({
            "id": i + 1,
            "text": text,
            "hint": f"请从以下标签中选择最合适的一个: {', '.join(labels)}",
        })
    return samples


def generate_ner(count: int, labels: list[str], **kwargs) -> list[dict]:
    """Generate NER (Named Entity Recognition) samples."""
    if not labels:
        labels = ["人名", "地名", "机构名", "时间", "数量"]

    templates = [
        "{name}在{city}的{org}工作，于{date}参加了重要会议。",
        "{org}于{date}宣布，将在{city}开设新的分支机构。",
        "据{org}消息，{name}将于{date}前往{city}开展调研工作。",
        "{name}是{org}的负责人，长期在{city}工作生活。",
        "{date}，{name}代表{org}在{city}签署了合作协议。",
    ]

    samples = []
    for i in range(count):
        template = random.choice(templates)
        text = template.format(
            name=fake.name(),
            city=fake.city(),
            org=fake.company(),
            date=fake.date_this_decade().strftime("%Y年%m月%d日"),
        )
        samples.append({
            "id": i + 1,
            "text": text,
            "hint": f"请标注文中的命名实体，可用标签: {', '.join(labels)}",
        })
    return samples


def generate_qa(count: int, **kwargs) -> list[dict]:
    """Generate QA (Question Answering) samples."""
    qa_pairs = [
        {
            "context": "人工智能（AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。",
            "question": "人工智能是什么学科的分支？",
        },
        {
            "context": "机器学习是人工智能的一个子集，它使用统计技术让计算机系统从数据中学习，而不需要明确编程。",
            "question": "机器学习和人工智能是什么关系？",
        },
        {
            "context": "深度学习是机器学习的一种，它使用多层神经网络来从数据中学习表示，已经在图像识别、语音识别、自然语言处理等领域取得了突破性进展。",
            "question": "深度学习在哪些领域取得了突破性进展？",
        },
        {
            "context": "自然语言处理（NLP）是人工智能的一个重要子领域，专注于计算机理解和生成人类语言的能力。",
            "question": "NLP是什么的缩写？它关注什么？",
        },
        {
            "context": "数据标注是机器学习训练数据准备的关键步骤，通过人工或半自动方式为原始数据添加标签，使模型能够从中学习。",
            "question": "数据标注在机器学习中起什么作用？",
        },
    ]

    samples = []
    for i in range(count):
        pair = qa_pairs[i % len(qa_pairs)]
        if i >= len(qa_pairs):
            pair = {
                "context": fake.paragraph(nb_sentences=3),
                "question": "请根据上文回答以下问题：" + fake.sentence(nb_words=8) + "？",
            }
        samples.append({
            "id": i + 1,
            "context": pair["context"],
            "question": pair["question"],
            "hint": "请根据上下文提供准确的答案",
        })
    return samples


def generate_instruction_tuning(count: int, **kwargs) -> list[dict]:
    """Generate instruction-tuning samples (instruction/input/output triples)."""
    instructions = [
        {
            "instruction": "将以下句子翻译成英文",
            "input": fake_en.sentence(),
            "hint": "请提供准确、自然的中文翻译",
        },
        {
            "instruction": "对以下文本进行摘要",
            "input": fake.paragraph(nb_sentences=5),
            "hint": "请用2-3句话概括主要内容",
        },
        {
            "instruction": "判断以下评论的情感倾向（正面/负面/中性）",
            "input": fake.sentence(nb_words=20),
            "hint": "请只回答：正面、负面或中性",
        },
        {
            "instruction": "改写以下句子，使其更加正式",
            "input": fake.sentence(nb_words=15),
            "hint": "保持原意，使用更正式的表达方式",
        },
        {
            "instruction": "列举以下概念的三个例子",
            "input": random.choice(["人工智能应用", "环保行为", "健康食品", "运动项目"]),
            "hint": "请列举三个具体的例子",
        },
    ]

    samples = []
    for i in range(count):
        tmpl = instructions[i % len(instructions)]
        samples.append({
            "id": i + 1,
            "instruction": tmpl["instruction"],
            "input": tmpl["input"],
            "hint": tmpl["hint"],
        })
    return samples


def generate_text_generation(count: int, **kwargs) -> list[dict]:
    """Generate text generation / completion samples."""
    prompts = [
        "请续写以下故事开头：从前有一个小村庄，村里住着一位神秘的老人...",
        "根据以下关键词写一段描述：科技、未来、城市、智能",
        "请为以下产品撰写一段广告语：一款新型智能手表",
        "写一封给朋友的信，主题是：分享最近学到的新技能",
        "根据以下主题写一首短诗：春天的到来",
    ]

    samples = []
    for i in range(count):
        samples.append({
            "id": i + 1,
            "prompt": prompts[i % len(prompts)],
            "hint": "请根据提示生成高质量的文本内容",
        })
    return samples


GENERATORS = {
    "text_classification": generate_text_classification,
    "ner": generate_ner,
    "qa": generate_qa,
    "instruction_tuning": generate_instruction_tuning,
    "text_generation": generate_text_generation,
}


def generate_samples(task_type: str, count: int, labels: list[str] = None, **kwargs) -> list[dict]:
    """Dispatch to the appropriate generator."""
    generator = GENERATORS.get(task_type, generate_text_classification)
    return generator(count=count, labels=labels or [], **kwargs)
