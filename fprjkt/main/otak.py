import spacy
from gensim.models import KeyedVectors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import re, os, joblib
from collections import defaultdict
from database import db
from database.db_pakar import Conflict

SAVED_MODELS_DIR = "data_latihan"
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

KMEANS_PATH = os.path.join(SAVED_MODELS_DIR, "trained_data.joblib")

def save_trained_data():
    data = {
        'kmeans': kmeans,
        'tfidf_vectorizer': tfidf_vectorizer,
        'example_vectors': example_vectors,
        'dynamic_replacements': dynamic_replacements
    }
    joblib.dump(data, KMEANS_PATH)
    print("💾 Model & data training disimpan!")

def load_trained_data():
    if os.path.exists(KMEANS_PATH):
        data = joblib.load(KMEANS_PATH)
        print("🔍 Model & data training dimuat dari cache")
        return data
    return None



nlp = spacy.blank("id")

stopword = {
    'saya', 'kamu', 'kami', 'kita', 'mereka', 'ini', 'itu', 'di', 'ke', 'dari',
    'dan', 'atau', 'tapi', 'yang', 'untuk', 'pada', 'oleh', 'adalah'
}
nlp.Defaults.stop_words.update(stopword)
nlp.Defaults.stop_words -= {'dengan', 'karena', 'tidak'}
patterns = [
    {
        "label": "ORG",
        "pattern": [
            {"LOWER": {"IN": [
                "organisasi", "struktur", "divisi", "tim", 
                "kelompok", "lembaga", "pengurus", "anggota",
                "ketua", "pembimbing", "mahasiswa", "senior", 
                "junior", "hierarki"
            ]}},
            {"LOWER": {"IN": [
                "internal", "akademik", "keuangan", "acara", 
                "inti", "organisasi","rapat_organisasi","divisi_acara","rapat_koordinasi"
            ]}, "OP": "?"}
        ]
    },
    
    {
        "label": "ACADEMIC",
        "pattern": [
            {"LOWER": {"IN": ["skripsi", "praktikum", "akademik", "kuliah", "refleksi", "studi", "penelitian","tugas", "kelas_praktikum"]}}
        ]
    },
    
    {
        "label": "EVENT",
        "pattern": [
            {"LOWER": {"IN": [
                "rapat", "proyek", "workshop", "forum", 
                "mediasi", "pelatihan", "koordinasi", "lokakarya"
            ]}}
        ]
    },
    
    {
        "label": "CONFLICT_ACTION",
        "pattern": [
            {"LEMMA": {"IN": [
                "protes", "tolak", "selisih", "tuntut", "keberatan", "persoalkan",
                "bingung", "ragu", "pilih", "tolak", "tidak setuju", "pertentangan"
            ]}}
        ]
    },
    
    {
        "label": "STRUCTURE",
        "pattern": [
            {"LOWER": {"IN": [
                "kebijakan", "pembagian", "tanggungjawab", 
                "prioritas", "visi", "misi", "keputusan","sistem_pembagian_kerja","pembagian"
            ]}}
        ]
    },
    {
        "label": "COMPLEX_CONFLICT",
        "pattern": [
            {"LOWER": {"IN": ["konflik", "masalah", "perselisihan"]}},
            {"LOWER": {"IN": ["antara", "dengan"]}, "OP": "?"},
            {"ENT_TYPE": "ORG"},
            {"LOWER": "dan", "OP": "?"},
            {"ENT_TYPE": "ORG"}
        ]
    },
    {
        "label": "RESOURCE",
        "pattern": [
            {"LOWER": {"IN": ["sumber daya", "alokasi", "anggaran", "fasilitas", "peralatan"]}}
        ]
    }
]
KONFLIK_KEYWORDS = {
    'konflik', 'masalah', 'perselisihan', 'pertikaian', 'sengketa',
    'perbedaan', 'perdebatan', 'protes', 'berselisih', 'memprotes',
    'menolak', 'dipermasalahkan', 'bingung', 'ragu', 'dilema', 'pilihan',
    'ketegangan', 'ketidaksepahaman', 'ketidakpuasan', 'pertentangan',
    'persengketaan', 'percekcokan', 'ketidaksepakatan', 'persaingan',
    'perebutan', 'konfrontasi', 'perpecahan', 'perbedaan pendapat',
    'konflik', 'kesulitan', 'bentrok', 'ketidakseimbangan','kendala' ,'tidak puas'
}

if "entity_ruler" not in nlp.pipe_names:
    ruler = nlp.add_pipe("entity_ruler")
    ruler.add_patterns(patterns)

id_model = KeyedVectors.load('model/cc.id.300.bin')

ACTION_VERBS_SEED_PATH = "action_verbs_seed.txt"

G = nx.DiGraph()
GRAPH_VERSION = 0

RELATION_WEIGHTS = {
    "cause": 1.2,
    "depends-on": 1.1,
    "resolve": 1.0,
    "is-a": 0.9
}

def get_all_conflicts():
    return Conflict.query.options(db.joinedload(Conflict.examples)).all()

def build_graph(version=0):
    global G, GRAPH_VERSION, dynamic_replacements, tfidf_vectorizer, kmeans, example_vectors

    saved_data = load_trained_data()
    if saved_data:
        kmeans = saved_data['kmeans']
        tfidf_vectorizer = saved_data['tfidf_vectorizer']
        example_vectors = saved_data['example_vectors']
        dynamic_replacements = saved_data['dynamic_replacements']
        return G  # Langsung return tanpa training ulang

    G.clear()
    print("🔄 Memulai training model...")

    with db.session.no_autoflush:
        conflict_examples = []
        conflicts = Conflict.query.all()

        for conflict in conflicts:
            conflict_examples.extend(conflict.examples)


        conflict_texts = [ex.content for ex in conflict_examples]
        if conflict_texts:
            tfidf_vectorizer = TfidfVectorizer()
            tfidf_matrix = tfidf_vectorizer.fit_transform(conflict_texts)
        else:
            tfidf_matrix = None
            tfidf_vectorizer = None

        example_vectors = []

        
        for example in conflict_examples:
            tokens = preprocess_input(example.content).split()
            vec = np.mean(
                [id_model[word].astype(np.float32) for word in tokens if word in id_model], 
                axis=0
            )
            if vec.size:
                example_vectors.append(vec)

        if example_vectors:
            try:
                if len(example_vectors) < 2:
                    kmeans = None
                else:
                    example_vectors_array = np.array(example_vectors, dtype=np.float32)
                    kmeans = KMeans(n_clusters=min(5, len(example_vectors_array)))
                    kmeans.fit(example_vectors_array)
            except Exception as e:
                print(f"KMeans error: {str(e)}")
                kmeans = None
        else:
            kmeans = None

        dynamic_replacements = generate_dynamic_replacements(conflict_examples, id_model)


        for conflict in conflicts:
            G.add_node(conflict.name, type="conflict")

            for example in conflict.examples:
                G.add_node(example.content, type="example")
                G.add_edge(example.content, conflict.name, relation="is-a")

            for solution in conflict.solutions:
                G.add_node(solution.content, type="solution")
                G.add_edge(conflict.name, solution.content, relation="resolve")

            for relation in conflict.relations:
                G.add_node(relation.content, type="attribute")
                G.add_edge(
                    conflict.name,
                    relation.content,
                    relation=relation.type,
                    weight=RELATION_WEIGHTS.get(relation.type, 1.0),
                )
        save_trained_data()
    GRAPH_VERSION += 1
    return G

def get_dynamic_synonyms(word, topn=3):
    if word in id_model:
        return [syn for syn, _ in id_model.most_similar(word, topn=topn)]
    return []

def generate_dynamic_replacements(conflict_examples, model, threshold=0.65):

    bigrams = set()
    for example in conflict_examples:
        raw_text = example.content.lower().replace(" ", "_")
        tokens = raw_text.split("_")
        bigrams.update(["_".join(tokens[i:i+2]) for i in range(len(tokens)-1)])
    
    replacements = {}
    for phrase in bigrams:
        phrase_nospace = phrase.replace(" ", "_")
        
        pattern = re.compile(rf'\b{phrase}\b', re.IGNORECASE)
        replacements[pattern] = phrase_nospace
        
        for word in phrase.split():
            if word in model:
                similar_words = model.most_similar(word, topn=5)
                for similar, score in similar_words:
                    if score >= threshold:
                        synonym_phrase = phrase.replace(word, similar)
                        pattern_synonym = re.compile(rf'\b{synonym_phrase}\b', re.IGNORECASE)
                        replacements[pattern_synonym] = phrase_nospace
    
    return replacements

def load_seed_action_verbs():
    if not os.path.exists(ACTION_VERBS_SEED_PATH):
        return set()
    with open(ACTION_VERBS_SEED_PATH, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines())

def expand_action_verbs(model, seed_verbs, threshold=0.6):
    expanded_verbs = set(seed_verbs)
    for verb in seed_verbs:
        if verb in model:
            similar_words = model.most_similar(verb, topn=20)
            for word, score in similar_words:
                if score >= threshold and word not in expanded_verbs:
                    expanded_verbs.add(word)
    return expanded_verbs

seed_verbs = load_seed_action_verbs()
action_verbs = expand_action_verbs(id_model, seed_verbs) if seed_verbs else set()

def preprocess_input(text):
    removal_patterns = [
        r'\b(entitas\s+terkait|struktur\s+internal|deskripsi\s+|terkait\s+)\b',
        r'\b(menurut\s+saya|menurut\s+pendapat\s+saya)\b',
        r'\b(secara\s+umum|pada\s+dasarnya|sebenarnya)\b'
    ]
    for pattern in removal_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    conflict_examples = []
    for conflict in Conflict.query.all():
        conflict_examples.extend(conflict.examples)

    dynamic_replacements = generate_dynamic_replacements(conflict_examples, id_model)

    default_replacements = {
        r'divisi\s+(\w+)': r'divisi_\1',
        r'kebijakan\s+baru': 'kebijakan_baru',
        r'(tidak\s+setuju)': 'tidak_setuju',
        r'komunikasi\s+lintas': 'komunikasi_lintas',
        r'(rapat|pertemuan)\s+(\w+)': r'rapat_\2',
        r'(tanggung\s*jawab|tugas)\s+(\w+)': r'tugas_\2',
        r'(deadline|batas\s*waktu)\s+(\w+)': r'deadline_\2',
        r'(konflik|masalah)\s+(\w+)': r'konflik_\2',
        r'keputusan\s+(sepihak|terburu\s*buru)': 'keputusan_terburu',
        r'(jadwal|waktu)\s+(bentrok|tabrakan)': 'jadwal_bentrok',
        r'(ketua|anggota)\s+organisasi': r'\1_organisasi'
    }

    for pattern, replacement in default_replacements.items():
        dynamic_replacements[re.compile(pattern, re.IGNORECASE)] = replacement

    for pattern, replacement in dynamic_replacements.items():
        text = pattern.sub(replacement, text)

    text = re.sub(r'[^\w\s,.]', '', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

def enhanced_similarity(text1, text2):
    if not tfidf_vectorizer:
        return 0.0

    try:
        vec1 = tfidf_vectorizer.transform([text1])
        vec2 = tfidf_vectorizer.transform([text2])
        tfidf_sim = (vec1 * vec2.T).toarray()[0][0]
    except:
        tfidf_sim = 0.0
    
    tokens1 = preprocess_input(text1).split()
    tokens2 = preprocess_input(text2).split()
    
    vec_embed1 = np.mean([id_model[word] for word in tokens1 if word in id_model], axis=0)
    vec_embed2 = np.mean([id_model[word] for word in tokens2 if word in id_model], axis=0)
    
    if vec_embed1.size and vec_embed2.size:
        embed_sim = np.dot(vec_embed1, vec_embed2) / (np.linalg.norm(vec_embed1) * np.linalg.norm(vec_embed2))
    else:
        embed_sim = 0
    
    return 0.6 * tfidf_sim + 0.4 * embed_sim

def is_conflict_context(text):
    if any(word in text.split() for word in KONFLIK_KEYWORDS):
        return True
    
    conflict_vectors = [id_model[word] for word in KONFLIK_KEYWORDS if word in id_model]
    
    if not conflict_vectors:
        return False
    
    words_in_model = [word for word in text.split() if word in id_model]
    if not words_in_model:
        return False
    
    text_vector = np.mean([id_model[word] for word in words_in_model], axis=0)
    return any(np.dot(text_vector, cv) > 0.4 for cv in conflict_vectors)
    
def calculate_similarity(text1, text2):
    expanded1 = expand_synonyms(text1)
    expanded2 = expand_synonyms(text2)
    
    tokens1 = set(expanded1.split())
    tokens2 = set(expanded2.split())
    
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    base_sim = len(intersection)/len(union) if union else 0
    
    entity_boost = 0
    if any(word in tokens1.union(tokens2) for word in ['divisi_keuangan', 'divisi_acara', 'kebijakan_baru']):
        entity_boost = 0.5
    
    return min(base_sim + entity_boost, 1.0)

def semantic_similarity(text1, text2):
    tokens1 = preprocess_input(text1).split()
    tokens2 = preprocess_input(text2).split()
    
    vec1 = np.mean([id_model[word] for word in tokens1 if word in id_model], axis=0)
    vec2 = np.mean([id_model[word] for word in tokens2 if word in id_model], axis=0)

    if vec1.size == 0 or vec2.size == 0:
        return 0.0
    
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)) if vec1.size and vec2.size else 0

def get_entity_patterns():
    pattern_details = []
    descriptions = {
        'ORG': 'Entitas terkait organisasi dan struktur internal',
        'GPE': 'Entitas geografis dan administratif',
        'EVENT': 'Kegiatan atau acara yang terjadwal',
    }
    
    for pattern in patterns:
        p_type = "Daftar Kata"
        examples = []
        
        first_token = pattern['pattern'][0]
        lower_info = first_token.get('LOWER')
        
        if lower_info:
            if 'REGEX' in lower_info:
                p_type = "Pola RegEx"
                examples = [lower_info['REGEX']]
            elif 'IN' in lower_info:
                examples = lower_info['IN']
        
        pattern_details.append({
            'label': pattern['label'],
            'type': p_type,
            'examples': examples,
            'description': descriptions.get(pattern['label'], 'Tidak ada deskripsi')
        })
    
    return pattern_details


def analyze_input(user_input):
    cleaned = preprocess_input(user_input)
    doc = nlp(cleaned)
    
    conflict_keywords = KONFLIK_KEYWORDS.intersection(cleaned.split())
    has_conflict_keywords = len(conflict_keywords) > 0
    
    entities_present = {
        'ORG': False,
        'ACADEMIC': False,
        'STRUCTURE': False
    }
    
    for ent in doc.ents:
        if ent.label_ in entities_present:
            entities_present[ent.label_] = True
    
    has_action_verb = any(
        token.text.lower() in action_verbs or
        token.lemma_.lower() in action_verbs
        for token in doc
    )
    
    is_relevant = (
        has_conflict_keywords and 
        (entities_present['ORG'] or entities_present['ACADEMIC'] or entities_present['STRUCTURE'])
    ) or has_action_verb
    
    return {
        'entities': [(ent.text, ent.label_) for ent in doc.ents],
        'verbs': [token.lemma_ for token in doc if token.pos_ == 'VERB'],
        'keywords': list(conflict_keywords),
        'is_relevant': is_relevant,
        'debug_info': {
            'processed_text': cleaned,
            'expanded_synonyms': expand_synonyms(cleaned),
            'dependency_tree': [(token.text, token.dep_) for token in doc],
            'action_verbs_used': list(action_verbs)  # Untuk debug
        }
    }

def detect_conflicts(user_input):
    cleaned_input = preprocess_input(user_input)
    analysis = analyze_input(cleaned_input)
    
    if not analysis['is_relevant']:
        return []
    
    all_examples = [example for conflict in Conflict.query.all() for example in conflict.examples]
    similarities = [enhanced_similarity(cleaned_input, example.content) for example in all_examples]
    
    if similarities:
        mean_sim = np.mean(similarities)
        std_sim = np.std(similarities) if len(similarities) > 1 else 0
        dynamic_threshold = max(0.1, mean_sim - 0.5 * std_sim)
    else:
        dynamic_threshold = 0.15
    
    def detect_org(text):
        tokens = text.split()
        org_keywords = {"divisi", "tim", "kelompok"}
        return [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1) if tokens[i] in org_keywords]
    
    detected_orgs = detect_org(cleaned_input)
    
    def get_relation_description(rel_type):
        descriptions = {
            'cause': 'Hubungan sebab-akibat (+20%)',
            'depends-on': 'Ketergantungan sistem (+10%)',
            'is-a': 'Hubungan hierarki (-10%)'
        }
        return descriptions.get(rel_type, 'Tidak ada pengaruh')
    
    depends_on_map = defaultdict(list)
    for conflict in Conflict.query.all():
        for rel in conflict.relations:
            if rel.type == 'depends-on':
                depends_on_map[conflict.name].append(rel.content.lower())
    
    relation_matches = defaultdict(list)
    for conflict, deps in depends_on_map.items():
        for dep in deps:
            if dep in cleaned_input:
                relation_matches[conflict].append(dep)
    
    conflicts = Conflict.query.all()
    candidates = []
    
    for conflict in conflicts:
        max_score = 0
        best_example = None
        debug_info = []
        rel_type = 'depends-on' if conflict.name in relation_matches else None
        
        for example in conflict.examples:
            current_sim = enhanced_similarity(cleaned_input, example.content)
            
            special_entities = ['divisi_keuangan', 'divisi_acara', 'kebijakan_baru', 'pembagian_tanggungjawab'] + detected_orgs
            tokens_combined = set(cleaned_input.split() + example.content.split())
            detected_entities = [word for word in special_entities if word in tokens_combined]
            
            entity_boost = 0.3 * len(detected_entities)
            weighted_sim = current_sim + entity_boost
            
            if conflict.name in relation_matches:
                relation_weight = RELATION_WEIGHTS.get("depends-on", 1.0)
                weighted_sim *= relation_weight
            
            if weighted_sim > max_score and weighted_sim > dynamic_threshold:
                max_score = weighted_sim
                debug_info = {
                    'input_tokens': cleaned_input.split(),
                    'example_tokens': example.content.split(),
                    'detected_entities': detected_entities,
                    'entity_count': len(detected_entities),
                    'relation_type': rel_type,
                    'relation_description': get_relation_description(rel_type) if rel_type else 'Tidak ada relasi',
                    'semantic_sim': current_sim,
                    'dynamic_threshold': dynamic_threshold
                }
                best_example = example.content

        if max_score > dynamic_threshold:
            candidates.append({
                'conflict': conflict,
                'score': max_score,
                'example': best_example,
                'relations': relation_matches.get(conflict.name, []),
                'debug': debug_info
            })
    # sini
    input_vector = np.mean(
        [id_model[word].astype(np.float32) for word in cleaned_input.split() if word in id_model],
        axis=0
    ).astype(np.float32)

    if input_vector.size and kmeans:
        try:
            input_vector_2d = np.array([input_vector], dtype=np.float32)
            cluster_id = kmeans.predict(input_vector_2d)[0]

            cluster_conflicts = []
            for c in candidates:
                for ex in c['conflict'].examples:
                    ex_tokens = preprocess_input(ex.content).split()
                    ex_vec = np.mean(
                        [id_model[word].astype(np.float32) for word in ex_tokens if word in id_model],
                        axis=0
                    ).astype(np.float32)
                    
                    if ex_vec.size:
                        ex_vec_2d = np.array([ex_vec], dtype=np.float32)
                        if kmeans.predict(ex_vec_2d)[0] == cluster_id:
                            cluster_conflicts.append(c)
                            break
            
            candidates = sorted(cluster_conflicts, key=lambda x: x['score'], reverse=True)
        
        except Exception as e:
            print(f"Error in clustering: {str(e)}")
    
    return sorted(candidates, key=lambda x: x['score'], reverse=True)

def expand_synonyms(text):
    tokens = text.split()
    expanded = []
    for token in tokens:
        expanded.append(token)
        expanded.extend(get_dynamic_synonyms(token))
    return ' '.join(list(set(expanded)))

def get_solutions_and_relations(conflict_name, user_input):
    cleaned_input = preprocess_input(user_input)
    solutions = []
    relations = []
    
    try:
        conflict = Conflict.query.filter_by(name=conflict_name).first()
        for solution in conflict.solutions:
            sol_text = preprocess_input(solution.content)
            sim = calculate_similarity(cleaned_input, sol_text)
            solutions.append((solution.content, sim))
        
        for neighbor in G.neighbors(conflict_name):
            edge_data = G.get_edge_data(conflict_name, neighbor)
            if edge_data['relation'] in ['cause', 'depends-on']:
                rel_text = preprocess_input(neighbor)
                sim = calculate_similarity(cleaned_input, rel_text)
                relations.append((neighbor, edge_data['relation'], sim))
        
        solutions = sorted(solutions, key=lambda x: x[1], reverse=True)
        relations = sorted(relations, key=lambda x: x[2], reverse=True)
        
    except Exception as e:
        print(f"error solusi: {e}")
    
    return solutions, relations

def generate_graph_image():
    plt.switch_backend('Agg')
    plt.figure(figsize=(15,10))
    pos = nx.spring_layout(G, k=0.5)
    nx.draw(G, pos, with_labels=True, node_size=2500, 
           node_color="skyblue", font_size=10, 
           edge_color="gray", width=1.5, arrowsize=15)
    plt.savefig('static/graph.png', bbox_inches='tight')
    plt.close()