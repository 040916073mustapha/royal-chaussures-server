with open('C:/Users/Micro-Tech/.openclaw/workspace/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the fallback route from the success branch
old_success_fallback = """    logger.info("[Store POS] DB teardown handler registered")
    
    # Direct POS fallback route
    @app.route('/api/v1/store/pos', methods=['GET'])
    def _pos_fallback():
        return render_template('pos/index.html')
    logger.info("[Store POS] POS fallback route registered")
    
except Exception as e:"""

new_success_fallback = """    logger.info("[Store POS] DB teardown handler registered")
    
except Exception as e:"""

if old_success_fallback in content:
    content = content.replace(old_success_fallback, new_success_fallback)
    print('1. Success fallback removed: OK')
else:
    print('1. Success fallback: NOT FOUND!')

with open('C:/Users/Micro-Tech/.openclaw/workspace/server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done!')
