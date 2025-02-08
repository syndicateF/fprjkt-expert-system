from flask import request, redirect, url_for, session, jsonify
from database.db_pakar import db, Conflict, Example, Solution, Relation
from . import syndicate

@syndicate.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('fprjkt.home'))


@syndicate.route('/hapus_konflik/<int:id_konflik>', methods=['POST'])
def hapus_konflik(id_konflik):
    konflik = Conflict.query.get(id_konflik)
    db.session.delete(konflik)
    db.session.commit()
    return redirect(url_for('fprjkt.conflicts'))



@syndicate.route('/submit_relations/<int:conflict_id>', methods=['POST'])
def submit_relations(conflict_id):
    try:
        # Debug: Cetak data yang diterima
        print(f"Received request with data: {request.get_data()}")
        
        conflict = Conflict.query.get(conflict_id)
        if not conflict:
            return jsonify({'message': 'Conflict not found!'}), 404

        data = request.get_json()
        print(f"Parsed JSON data: {data}")  # Debugging
        
        # Ambil data dari payload JSON
        cause_list = data.get('cause', [])
        depends_on_list = data.get('depends_on', [])
        resolve_list = data.get('resolve', [])

        # Dapatkan relasi yang sudah ada
        existing_relations = Relation.query.filter_by(conflict_id=conflict_id).all()
        
        # Fungsi helper untuk sinkronisasi
        def sync_relations(new_contents, relation_type):
            # Filter relasi yang ada berdasarkan type
            existing = [rel for rel in existing_relations if rel.type == relation_type]
            
            # Hapus relasi yang tidak ada di data baru
            for rel in existing:
                if rel.content not in new_contents:
                    db.session.delete(rel)
            
            # Tambahkan relasi baru
            for content in new_contents:
                content = content.strip()
                if content and not any(rel.content == content for rel in existing):
                    new_rel = Relation(
                        type=relation_type,
                        content=content,
                        conflict_id=conflict_id
                    )
                    db.session.add(new_rel)

        # Proses semua tipe relasi
        sync_relations(cause_list, 'cause')
        sync_relations(depends_on_list, 'depends_on')
        sync_relations(resolve_list, 'resolve')

        db.session.commit()
        
        return jsonify({
            'message': 'Relations updated successfully!',
            'updated': {
                'cause': cause_list,
                'depends_on': depends_on_list,
                'resolve': resolve_list
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")  # Debugging
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@syndicate.route('/submit_solutions/<int:conflict_id>', methods=['POST'])
def submit_solutions(conflict_id):
    try:
        conflict = Conflict.query.get(conflict_id)
        if not conflict:
            return jsonify({'message': 'Conflict not found!'}), 404

        solution_list = request.form.getlist(f'solution-{conflict_id}[]')

        existing_solutions = Solution.query.filter_by(conflict_id=conflict_id).all()

        # Sinkronisasi solusi
        for solution in existing_solutions:
            if solution.content not in solution_list:
                db.session.delete(solution)

        for content in solution_list:
            if content.strip() and not any(sol.content == content.strip() for sol in existing_solutions):
                db.session.add(Solution(content=content.strip(), conflict_id=conflict_id))

        db.session.commit()
        return jsonify({'message': 'Solutions updated successfully!'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500




@syndicate.route('/update/<string:field_type>/<int:conflict_id>', methods=['POST'])
def update_conflict_field(field_type, conflict_id):
    try:
        data = request.get_json()
        conflict = Conflict.query.get(conflict_id)
        field_mapping = {
            'nama': 'name',
            'saran': 'saran'
        }
        if field_type not in field_mapping:
            return jsonify({'message': 'Field tidak valid!'}), 400
        new_value = data.get(field_type)
        setattr(conflict, field_mapping[field_type], new_value.strip())
        db.session.commit()
        return jsonify({'message': 'Update berhasil!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500
    
# CRUD ex
@syndicate.route('/example/create/<int:conflict_id>', methods=['POST'])
def create_example(conflict_id):
    data = request.get_json()
    new_example = Example(
        content=data['content'],
        conflict_id=conflict_id
    )
    db.session.add(new_example)
    db.session.commit()
    return jsonify({'message': 'Example created!'}), 201

@syndicate.route('/example/update/<int:example_id>', methods=['PUT'])
def update_example(example_id):
    example = Example.query.get_or_404(example_id)
    data = request.get_json()
    example.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Example updated successfully'}), 200

@syndicate.route('/example/delete/<int:example_id>', methods=['DELETE'])
def delete_example(example_id):
    example = Example.query.get_or_404(example_id)
    db.session.delete(example)
    db.session.commit()
    return jsonify({'message': 'Example deleted!'}), 200

# CRUD solusi
@syndicate.route('/solusi/create/<int:conflict_id>', methods=['POST'])
def create_solution(conflict_id):
    data = request.get_json()
    new_example = Solution(
        content=data['content'],
        conflict_id=conflict_id
    )
    db.session.add(new_example)
    db.session.commit()
    return jsonify({'message': 'Solution created!'}), 201

@syndicate.route('/solusi/update/<int:example_id>', methods=['PUT'])
def update_solution(example_id):
    example = Solution.query.get_or_404(example_id)
    data = request.get_json()
    example.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Solution updated successfully'}), 200

@syndicate.route('/solusi/delete/<int:example_id>', methods=['DELETE'])
def delete_solution(example_id):
    example = Solution.query.get_or_404(example_id)
    db.session.delete(example)
    db.session.commit()
    return jsonify({'message': 'Solution deleted!'}), 200







@syndicate.route('/<type>/create/<int:conflict_id>', methods=['POST'])
def create_relation(type, conflict_id):
    data = request.get_json()
    new_relation = Relation(
        content=data['content'],
        type=type.replace('-', '_'),
        conflict_id=conflict_id
    )
    db.session.add(new_relation)
    db.session.commit()
    return jsonify({'message': 'Relation created!'}), 201

@syndicate.route('/relation/update/<int:relation_id>', methods=['PUT'])
def update_relation(relation_id):
    relation = Relation.query.get_or_404(relation_id)
    data = request.get_json()
    relation.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Relation updated!'}), 200

@syndicate.route('/relation/delete/<int:relation_id>', methods=['DELETE'])
def delete_relation(relation_id):
    relation = Relation.query.get_or_404(relation_id)
    db.session.delete(relation)
    db.session.commit()
    return jsonify({'message': 'Relation deleted!'}), 200





@syndicate.route('/add_conflict', methods=['POST'])
@syndicate.route('/update_conflict/<int:conflict_id>', methods=['PUT'])
def handle_conflict(conflict_id=None):
    try:
        data = request.get_json()
        
        if request.method == 'POST':
            conflict = Conflict(
                name=data['name'],
                saran=data['saran']
            )
            db.session.add(conflict)
            db.session.flush()
        else:
            conflict = Conflict.query.get_or_404(conflict_id)
            conflict.name = data['name']
            conflict.saran = data['saran']

        if 'examples' in data:
            Example.query.filter_by(conflict_id=conflict.id).delete()
            for example_content in data['examples']:
                if example_content.strip():
                    example = Example(
                        content=example_content.strip(),
                        conflict_id=conflict.id
                    )
                    db.session.add(example)

        if 'solutions' in data:
            Solution.query.filter_by(conflict_id=conflict.id).delete()
            for solution_content in data['solutions']:
                if solution_content.strip():
                    solution = Solution(
                        content=solution_content.strip(),
                        conflict_id=conflict.id
                    )
                    db.session.add(solution)

        if 'relations' in data:
            Relation.query.filter_by(conflict_id=conflict.id).delete()
            for rel_type in ['cause', 'depends_on', 'resolve']:
                for content in data['relations'].get(rel_type, []):
                    if content.strip():
                        relation = Relation(
                            type=rel_type,
                            content=content.strip(),
                            conflict_id=conflict.id
                        )
                        db.session.add(relation)

        db.session.commit()
        
        return jsonify({
            'message': 'Conflict saved successfully',
            'conflict_id': conflict.id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500