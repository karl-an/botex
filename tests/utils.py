import os
import csv
import json
from numbers import Number

import botex

OTREE_STARTUP_WAIT = 3

def delete_botex_db(botex_db = "tests/botex.sqlite3"):
    try:
        os.remove(botex_db)
    except OSError:
        pass

def delete_otree_db():
    try:
        os.remove("tests/otree/db.sqlite3")
    except OSError:
        pass    

def init_otree_test_session(botex_db = "tests/botex.sqlite3"):
    botex_session = botex.init_otree_session(
        config_name="botex_test", npart=2, botex_db = botex_db, 
    )
    return botex_session

def export_otree_data(csv_file, session_id=None):
    botex.export_otree_data(csv_file)
    assert os.path.exists(csv_file)
    with open(csv_file) as f:
        participants = list(csv.DictReader(f))
    # Wenn keine session_id übergeben, aus CSV ermitteln
    if session_id is None:
        session_codes = {p.get('session.code') for p in participants}
        assert len(session_codes) == 1, f"Erwartet genau einen Session-Code, gefunden: {session_codes}"
        session_id = session_codes.pop()
    # Filtere nur Einträge für diese Session
    session_participants = [p for p in participants if p.get('session.code') == session_id]
    assert len(session_participants) == 2, f"Expected 2 participants, found {len(session_participants)} for session {session_id}"
    for p in session_participants:
        assert p['participant._current_page_name'] == 'Thanks'

import tempfile

def normalize_otree_data(csv_file, session_id): # Add session_id parameter
    # Read original CSV
    with open(csv_file, 'r', encoding='utf-8-sig') as f_in:
        reader = csv.reader(f_in)
        all_rows = list(reader)

    if not all_rows:
        raise ValueError(f"Input CSV file {csv_file} is empty.")

    header = all_rows[0]
    data_rows = all_rows[1:]

    # Find the index of the session.code column
    try:
        session_code_index = header.index('session.code')
    except ValueError:
        # Try participant.session.code as fallback
        try:
            session_code_index = header.index('participant.session.code')
        except ValueError:
            raise ValueError(f"'session.code' or 'participant.session.code' column not found in {csv_file}")


    # Filter rows for the specific session_id
    filtered_rows = [header] + [row for row in data_rows if row[session_code_index] == session_id]

    if len(filtered_rows) <= 1:
         # Only header or no data for this session
         logger.warning(f"No data found for session {session_id} in {csv_file}. Skipping normalization checks for this file.")
         # Return an empty structure or handle as appropriate
         # For the test, we expect data, so maybe let it fail later if needed,
         # but create empty temp file to avoid error in normalize_otree_data
         filtered_rows = [header]


    # Write filtered data to a temporary file
    temp_csv_path = None # Initialize to ensure it's defined in finally block
    temp_csv_path = None # Initialize to ensure it's defined in finally block
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8-sig') as temp_f:
            writer = csv.writer(temp_f)
            writer.writerows(filtered_rows)
            temp_csv_path = temp_f.name

        # Call botex.normalize_otree_data with the temporary file
        dta = botex.normalize_otree_data(
            temp_csv_path, # Use temp file
            store_as_csv=True,
            data_exp_path="tests",
            exp_prefix="test"
        )
        df_names = ['participant', 'session', 'group', 'player']
        csv_file_names = ["test_" + dfn + ".csv" for dfn in df_names]
        for cfn in csv_file_names:
            assert os.path.exists(f"tests/{cfn}")
        assert isinstance(dta, dict)
        assert len(dta) == 4
        assert list(dta.keys()) == df_names
        assert len(dta['participant']) == 2
        assert list(dta['participant'][0].keys()) == \
            ['participant_code', 'current_app', 'current_page', 'time_started_utc']
        assert len(dta['session']) == 2
        assert list(dta['session'][0].keys()) == ['session_code', 'participant_code']
        assert len(dta['group']) == 1
        assert list(dta['group'][0].keys()) == [
            'session_code', 'round', 'string_field', 'integer_field',
            'boolean_field', 'choice_integer_field', 'radio_field',
            'float_field', 'feedback'
        ]
        assert len(dta['player']) == 2
        assert list(dta['player'][0].keys()) == [
            'participant_code', 'round', 'player_id', 'payoff', 'button_radio',
            'role'
        ]
        # --- Re-run normalization with var_dict using the same filtered temp file ---
        # This part seems redundant for just checking the participant count,
        # but keeping the structure similar to the original test helper.
        # If var_dict processing is essential for later tests, it should use temp_csv_path.
        var_dict_to_use={
                'participant': {
                    'code': 'participant_code',
                    'time_started_utc': 'time_started_utc'
                },
                'session': {
                    'code': 'session_code'
                },
                'botex_test': {
                    'player': {
                        'payoff': 'payoff',
                        'button_radio': 'bttn_radio',
                    }
                }
            }
        dta_vardict = botex.normalize_otree_data(
            temp_csv_path, # Use temp file again
            store_as_csv=True, # Re-saving might overwrite, consider different prefix or path if needed
            data_exp_path="tests",
            var_dict=var_dict_to_use,
            exp_prefix="test_vardict" # Use different prefix to avoid overwrite
        )
        # Assertions for the vardict run (adjust as needed based on expected output)
        # Example: Check if the remapped column exists
        assert 'bttn_radio' in dta_vardict['player'][0]
        assert list(dta_vardict['player'][0].keys()) == [
             'participant_code', 'round', 'player_id', 'payoff', 'bttn_radio'
         ]

    # Clean up the temporary file
    finally:
        if temp_csv_path and os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)


def get_model_provider(model):
    if "llamacpp" in model:
        return "llamacpp"
    if '/' in model:
        return model.split('/')[0]
    return "openai"

def create_answer_message(model):
    if model == "llamacpp":
        type = model
    else:
        type = get_model_provider(model)
    csv_file = f"tests/questions_and_answers_{type}.csv"
    if not os.path.exists(csv_file):
        return ""
    with open(csv_file) as f:
        quest_answers = list(csv.DictReader(f))
    am = ""
    for qa in quest_answers:
        am += (
            f"Question: '{qa['question']}'\n" +  
            f"Answer: '{qa['answer']}'\n" + 
            f"Rationale: '{qa['reason']}'\n\n"
        )
    return am[:-1]

def check_conversation_and_export_answers(model, session_id):
    type = get_model_provider(model)
    def add_answer_and_reason(qtext, id_, a):
        for i,qst in enumerate(qtext):
            if qst['id'] == id_ and 'answer' not in qst.keys():
                qtext[i]['answer'] = a['answer']
                qtext[i]['reason'] = a['reason']
                break
    
    err_start = [
        'I am sorry', 'Unfortunately', 'Your response was not valid'
    ]
    convs = botex.read_conversations_from_botex_db(
        botex_db="tests/botex.sqlite3", session_id=session_id
    )
    with open("tests/questions.csv") as f:
        qtexts = list(csv.DictReader(f))
        qids = [q['id'] for q in qtexts]
    
    answers = []
    for c in convs:
        assert isinstance(c['id'], str)
        assert isinstance(c['bot_parms'], str) 
        assert isinstance(c['conversation'], str)
        bot_parms = json.loads(c['bot_parms'])
        assert isinstance(bot_parms, dict)
        conv = json.loads(c['conversation'])
        assert isinstance(conv, list)
        for i, m in enumerate(conv):
            if i+2 < len(conv) and conv[i+1]['role'] == 'user':
                    if any(conv[i + 1]['content'].startswith(prefix) for prefix in err_start):
                        continue
            assert isinstance(m, dict)
            assert isinstance(m['role'], str)
            assert isinstance(m['content'], str)
            if m['role'] == 'assistant':
                try:
                    r = m['content']
                    start = r.find('{', 0)
                    end = r.rfind('}', start)
                    r = r[start:end+1]
                    r = json.loads(r, strict=False)
                except:
                    break
                if 'answers' in r:
                    qs = r['answers']
                    assert isinstance(qs, dict)
                    for a in qs:
                        answers.append({a: qs[a]})
    ids = []
    for a in answers:
        id_ = list(a.keys())[0]
        a = a[id_]
        assert isinstance(a, dict)
        assert isinstance(id_, str)
        assert isinstance(a['reason'], str)
        assert a['answer'] is not None
        ids.append(id_)
        if id_ == "id_integer_field": 
            assert isinstance(a['answer'], str) or isinstance(a['answer'], int)
        elif id_ == "id_float_field":
            assert isinstance(a['answer'], str) or isinstance(a['answer'], Number)
        elif id_ == "id_boolean_field":
            assert isinstance(a['answer'], str) or isinstance(a['answer'], bool)
        elif id_ in [
            "id_string_field", "id_feedback",
            "id_choice_integer_field", "id_button_radio"
        ]:
            assert isinstance(a['answer'], str)
        add_answer_and_reason(qtexts, id_, a)

    assert len(ids) == len(qids)    
    assert set(ids) == set(qids)
    with open(f"tests/questions_and_answers_{type}.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=qtexts[0].keys())
        writer.writeheader()
        writer.writerows(qtexts)


    

