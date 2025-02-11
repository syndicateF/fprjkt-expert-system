
from flask import render_template, request, flash, redirect, url_for, session, make_response, jsonify
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from database.db_pakar import User, db, Riwayat, Conflict, Example, Solution, Relation
from collections import defaultdict
from fprjkt.main.bundu import registrasi, login, simpan_riwayat, username_exists
from fprjkt.main.otak import GRAPH_VERSION, build_graph, detect_conflicts, analyze_input,get_solutions_and_relations,preprocess_input,generate_graph_image, get_entity_patterns, nlp, RELATION_WEIGHTS
from . import syndicate

page_positions = {
    "home": 0,
    "riwayat": 30,
    "regis": 60,
    "dashboard": 90,
    "add_conlict": 120,
    "conflicts": 150
}

@syndicate.route('/', methods=['GET', 'POST'])
def home():
    entity_patterns = get_entity_patterns()
    if request.method == 'POST':
        user_input = request.form['apa']
        session['masalah'] = user_input
        try:
            plt.close('all')
            db.session.rollback()
            build_graph()
            
            result = {
                "input": user_input,
                "conflicts": [],
                "solutions": [],
                "relations": [],
                "graph_image": False,
                "log": {
                    'dependency_matches': [],
                    'processed_input': '',
                    'keywords_found': [],
                    'matched_patterns': []
                },
                "error": None,
                "warning": None,
                "patterns": entity_patterns
            }

            analysis = analyze_input(user_input)
            result['analysis'] = analysis
            result['log']['processed_input'] = preprocess_input(user_input)
            result['log']['keywords_found'] = analysis['keywords']
            result['relations_weights'] = RELATION_WEIGHTS

            doc = nlp(user_input)
            matched_entities = [(ent.text, ent.label_) for ent in doc.ents]
            result['log']['matched_patterns'] = matched_entities
            
            if not analysis.get('is_relevant', False):
                result['warning'] = {
                    'title': 'Input Tidak Relevan',
                    'message': 'Sistem hanya memproses input terkait konflik organisasi',
                    'examples': [
                        "Contoh input valid:",
                        "1. Perselisihan antara divisi acara dan keuangan",
                        "2. Kesulitan membagi waktu antara organisasi dan akademik",
                        "3. Protes anggota terhadap kebijakan baru"
                    ]
                }
                return render_with_sidebar('home', result=result,RELATION_WEIGHTS=RELATION_WEIGHTS)
            
            detected_conflicts = detect_conflicts(user_input)
            
            if not detected_conflicts:  
                result['warning'] = {
                    'title': 'Konflik Tidak Ditemukan',
                    'message': 'Sistem tidak menemukan pola konflik yang sesuai',
                    'suggestions': [
                        "Gunakan kata kunci seperti: perselisihan, konflik, masalah",
                        "Deskripsikan setidaknya 2 pihak/objek yang terlibat",
                        "Contoh: 'Ketegangan antara senior dan junior tentang pembagian tugas'"
                    ]
                }
                return render_with_sidebar('home', result=result,RELATION_WEIGHTS=RELATION_WEIGHTS)
            
            top_conflicts = detected_conflicts[:3]
            
            all_solutions = []
            all_relations = []
            for conflict in top_conflicts:
                if isinstance(conflict, dict) and 'conflict' in conflict:
                    solutions, relations = get_solutions_and_relations(
                        conflict['conflict'].name,
                        user_input
                    )
                    all_solutions.extend(solutions)
                    all_relations.extend(relations)
                    
                    if 'relations' in conflict:
                        result['log']['dependency_matches'].extend(conflict['relations'])


            if not all_solutions:
                result['warning'] = {
                    'title': 'Solusi Tidak Ditemukan',
                    'message': 'Sistem tidak dapat menemukan solusi yang sesuai',
                    'suggestions': [
                        "Coba deskripsikan konflik lebih detail",
                        "Fokus pada tindakan atau hubungan antar pihak"
                    ]
                }
            
            result['solutions'] = sorted(
                {s[0]: s for s in all_solutions}.values(),
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            result['relations'] = sorted(
                {r[0]: r for r in all_relations}.values(),
                key=lambda x: x[2],
                reverse=True
            )[:5]

            result['conflicts'] = [{
                'name': c['conflict'].name if isinstance(c, dict) else 'Unknown',
                'score': c.get('score', 0),
                'base_sim': c.get('base_sim', 0),
                'entity_boost': c.get('entity_boost', 0),
                'relation_weight': c.get('relation_weight', 1.0),
                'example': c.get('example', ''),
                'relations': c.get('relations', []),
                'debug': {
                    **c.get('debug', {}),
                    'semantic_sim': c.get('debug', {}).get('semantic_sim', 0)
                }
            } for c in top_conflicts if isinstance(c, dict)]
            
            try:
                generate_graph_image()
                result['graph_image'] = True
            except Exception as e:
                print(f"Graph generation error: {e}")
                result['error'] = 'Gagal membuat visualisasi hubungan konflik'
            
            result['log'].update({
                'processed_input': preprocess_input(user_input),
                'keywords_found': analysis.get('keywords', []),
                'action_verbs_detected': analysis.get('debug_info', {}).get('action_verbs_used', [])
            })
            
            plt.close('all')
            return render_with_sidebar('home', result=result,RELATION_WEIGHTS=RELATION_WEIGHTS)
        
        except Exception as e:
            db.session.rollback()
            print(f"System error: {e}")
            result['error'] = f'Terjadi kesalahan sistem: {str(e)}'
            result['patterns'] = entity_patterns
            result['conflicts'] = []
            result['solutions'] = []
            result['relations'] = []
            return render_with_sidebar(
                'home', 
                result=result,
                patterns=entity_patterns,
                RELATION_WEIGHTS=RELATION_WEIGHTS
            )
        finally:
            db.session.close()
    return render_with_sidebar('home',patterns=entity_patterns,RELATION_WEIGHTS=RELATION_WEIGHTS)


@syndicate.route('/riwayat')
def riwayat():
    if 'login' not in session:
        flash('Loginko ko dulu su')
        return redirect(url_for('fprjkt.rute_login'))
    
    panjultzy = session['login']
    riwayat = Riwayat.query.filter_by(user_id=panjultzy).all()

    return render_with_sidebar('riwayat', riwayat=riwayat)

@syndicate.route('/regis', methods=['POST', 'GET'])
def regis():
    try:
        if request.method == 'POST':
            regis_form = request.form
            proses = registrasi(regis_form)

            kawan_baru = User(nama_depan=proses['nama_depan'],
                              nama_belakang=proses['nama_belakang'],
                              username=proses['username'],
                              password=proses['password'],
                              email=proses['email'])

            db.session.add(kawan_baru)
            db.session.commit()
            flash('oke', 'y')
            redirect(url_for('fprjkt.regis'))
    except Exception as e:
            flash(e, 'g')

    return render_with_sidebar('regis')

@syndicate.route('/login', methods=['POST', 'GET'])
def rute_login():
    try:
        if request.method == 'POST':
            data = request.get_json()  #  json dari req
            username = data.get('username')
            password = data.get('password')

            kawan = User.query.filter_by(username=username).first()

            if not kawan:
                return {'success': False, 'error': 'username'}, 400

            if kawan.password != password:
                return {'success': False, 'error': 'password'}, 400

            session['login'] = kawan.id
            session['nama_lengkap'] = f"{kawan.nama_depan} {kawan.nama_belakang}"
            return {'success': True}, 200
    except Exception as e:
        return {'success': False, 'error': 'server', 'message': str(e)}, 500

    return render_with_sidebar('login')



@syndicate.route('/dashboard')
def dashboard():
    hamzah = User.query.all()
    return render_with_sidebar('dashboard', hamzah=hamzah)

@syndicate.route('/add_conlict', methods=['GET', 'POST'])
def add_conlict():
    try:
        if request.method == 'POST':
            name = request.form['name']
            saran = request.form['saran']
            conflict = Conflict(name=name, saran=saran)
            db.session.add(conflict)
            db.session.commit()

            examples = request.form.getlist('examples[]')
            for example_content in examples:
                example = Example(content=example_content, conflict_id=conflict.id)
                db.session.add(example)

            solutions = request.form.getlist('solutions[]')
            for solution_content in solutions:
                solution = Solution(content=solution_content, conflict_id=conflict.id)
                db.session.add(solution)

            cause_list = request.form.getlist('cause[]')
            dependson_list = request.form.getlist('depends_on[]')
            resolve_list = request.form.getlist('resolve[]')

            for cause, dependson, resolve in zip(cause_list, dependson_list, resolve_list):
                if cause:
                    relation = Relation(type='cause', content=cause, conflict_id=conflict.id)
                    db.session.add(relation)
                if dependson:
                    relation = Relation(type='depends-on', content=dependson, conflict_id=conflict.id)
                    db.session.add(relation)
                if resolve:
                    relation = Relation(type='resolve', content=resolve, conflict_id=conflict.id)
                    db.session.add(relation)

            db.session.commit()

            flash('ok')
    except Exception as e:
        flash(e)
    return render_with_sidebar('add_conlict')

@syndicate.route('/conflicts')
def conflicts():
    semua_konflik = Conflict.query.all()
    for conflict in semua_konflik:
        relations_by_type = defaultdict(list)
        for relation in conflict.relations:
            relations_by_type[relation.type].append(relation)
    
        conflict.relations_by_type = relations_by_type
    return render_with_sidebar('conflicts',semua_konflik=semua_konflik, relations_by_type=relations_by_type)



def render_with_sidebar(current_page,
                        masalah=None,
                        result=None,
                        patterns=None,
                        riwayat=None,
                        
                        hamzah=None,
                        
                        semua_konflik=None,
                        relations_by_type=None,
                        RELATION_WEIGHTS=None):
    old_page = request.cookies.get("last_page", "home")
    
    old_position = page_positions.get(old_page, 0)
    new_position = page_positions.get(current_page, 0)

    response = make_response(render_template(
        f"{current_page}.html",
        active_page=current_page,
        old_position=old_position,
        new_position=new_position,

        masalah=masalah,
        result=result,
        patterns=patterns,
        riwayat=riwayat,
        
        hamzah=hamzah,
        relations_by_type=relations_by_type,
        RELATION_WEIGHTS=RELATION_WEIGHTS,
        semua_konflik=semua_konflik
    ))

    response.set_cookie("last_page", current_page)

    return response