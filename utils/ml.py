import re
import math

CATEGORIES = {
    "Research": ["research", "abstract", "study", "analysis", "paper", "hypothesis", "conclusion", "experiment"],
    "Legal": ["contract", "agreement", "lease", "policy", "legal", "terms", "conditions", "law", "court", "liability"],
    "Finance": ["invoice", "receipt", "budget", "finance", "revenue", "expense", "profit", "tax", "payment", "account", "investment", "audit"],
    "Tech & Code": ["code", "programming", "python", "javascript", "html", "css", "database", "blockchain", "api", "software", "development", "git"],
    "Education": ["assignment", "homework", "syllabus", "lecture", "course", "lesson", "student", "teacher", "exam", "grade"],
    "Personal": ["diary", "note", "letter", "todo", "list", "ideas", "journal", "memories", "photos"]
}

def tokenize(text):
    return re.findall(r'\w+', text.lower())

def get_freq_dict(tokens):
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    return freq

def cosine_similarity(text1, text2):
    """
    Computes cosine similarity between two texts using a lightweight TF-IDF/bag-of-words implementation in pure Python.
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    freq1 = get_freq_dict(tokens1)
    freq2 = get_freq_dict(tokens2)
    
    all_tokens = set(freq1.keys()) | set(freq2.keys())
    
    dot_product = 0.0
    sum_sq1 = 0.0
    sum_sq2 = 0.0
    
    for t in all_tokens:
        val1 = freq1.get(t, 0)
        val2 = freq2.get(t, 0)
        dot_product += val1 * val2
        sum_sq1 += val1 * val1
        sum_sq2 += val2 * val2
        
    if sum_sq1 == 0 or sum_sq2 == 0:
        return 0.0
        
    return dot_product / (math.sqrt(sum_sq1) * math.sqrt(sum_sq2))

def generate_tags(text, filename):
    """
    Categorizes the document based on extension rules and keyword term frequencies.
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    tags = []
    
    if ext in ['py', 'js', 'html', 'css', 'json', 'sh', 'sql']:
        tags.append("Code")
        tags.append("Tech")
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        tags.append("Image")
        tags.append("Media")
    elif ext in ['pdf', 'docx', 'doc', 'txt']:
        tags.append("Document")
        
    text_lower = text.lower()
    scores = {cat: 0 for cat in CATEGORIES}
    
    for category, keywords in CATEGORIES.items():
        for word in keywords:
            scores[category] += len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
            
    matched_categories = [cat for cat, score in scores.items() if score > 0]
    matched_categories.sort(key=lambda x: scores[x], reverse=True)
    
    tags.extend(matched_categories[:2])
    unique_tags = list(dict.fromkeys(tags))
    
    if not unique_tags:
        unique_tags.append("General")
        
    return ", ".join(unique_tags)
