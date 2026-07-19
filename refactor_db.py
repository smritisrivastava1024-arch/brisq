import re

with open('database.py', 'r') as f:
    content = f.read()

# 1. Update get_connection to be a context manager
old_conn = '''def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn'''

new_conn = '''from contextlib import contextmanager

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()'''

content = content.replace(old_conn, new_conn)

# 2. Add docstring to initialize_database, add indexes, add schema_version
old_init = '''def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()'''

new_init = '''def initialize_database():
    """
    Initializes the database schema.
    This function is completely idempotent and safe to run on every app startup.
    It uses CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS, ensuring
    it only adds missing structures without dropping existing data.
    """
    with get_connection() as conn:
        cursor = conn.cursor()'''

content = content.replace(old_init, new_init)

# Fix initialize_database internal structure
init_body_match = re.search(r'(?<=        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n    \)\n    """)\n\n    cursor\.execute\("""\n    CREATE TABLE IF NOT EXISTS approvals \()(.*?)(?=\)\n    """\)\n\n    conn\.commit\(\)\n    conn\.close\(\))', content, flags=re.DOTALL)

if init_body_match:
    approvals_cols = init_body_match.group(1)
    
    new_init_tail = f'''{approvals_cols})
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_abandoned_carts_status ON abandoned_carts(approved, sent)")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    )
    """)
    cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (1)")

    conn.commit()'''
    
    content = content[:init_body_match.start()] + new_init_tail + content[init_body_match.end()+31:]
    # The +31 is to skip `)\n    """)\n\n    conn.commit()\n    conn.close()`

# 3. Refactor all other functions to use `with get_connection() as conn:`
funcs = [
    'create_abandoned_cart', 'get_pending_abandoned_carts', 'get_abandoned_cart_by_token',
    'update_abandoned_cart_ai_messages', 'approve_abandoned_cart', 'reject_abandoned_cart',
    'mark_abandoned_cart_sent', 'mark_abandoned_cart_recovered', 'create_approval',
    'get_pending_approvals', 'get_all_approvals', 'approve_request', 'reject_request'
]

for func in funcs:
    pattern = r'(def ' + func + r'\(.*?\):\n)\s*conn = get_connection\(\)\n\s*cursor = conn\.cursor\(\)\n(.*?)(?:\s*conn\.commit\(\))?\n\s*conn\.close\(\)'
    
    def repl(m):
        header = m.group(1)
        body = m.group(2)
        has_commit = 'conn.commit()' in m.group(0)
        
        lines = body.strip().split('\n')
        new_body = '    with get_connection() as conn:\n        cursor = conn.cursor()\n'
        for line in lines:
            if line:
                new_body += '        ' + line + '\n'
            else:
                new_body += '\n'
                
        if has_commit:
            new_body += '\n        conn.commit()\n'
            
        return header + new_body
        
    content = re.sub(pattern, repl, content, flags=re.DOTALL)

# Handle cases where conn.close() was before return, e.g. get_pending_abandoned_carts
def cleanup_returns(match):
    header = match.group(1)
    body = match.group(2)
    # indent body by 4 spaces
    indented_body = '\n'.join('        ' + line if line else '' for line in body.split('\n'))
    
    return f"{header}    with get_connection() as conn:\n        cursor = conn.cursor()\n{indented_body}"

content = re.sub(r'(def (?:get_pending_abandoned_carts|get_abandoned_cart_by_token|get_pending_approvals|get_all_approvals)\(.*?\):\n)\s*conn = get_connection\(\)\n\s*cursor = conn\.cursor\(\)\n(.*?)\s*conn\.close\(\)', cleanup_returns, content, flags=re.DOTALL)

with open('database.py', 'w') as f:
    f.write(content)

print("database.py refactored.")
