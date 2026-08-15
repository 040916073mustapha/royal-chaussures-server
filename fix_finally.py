import ast

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the 'finally:' block entirely - replace with just close after conn on all paths
old1 = '        finally:\n            try:\n                conn.close()\n            except:\n                pass'
new1 = ''

# Actually, let's replace the entire upsert finally with a simpler approach
# Replace the except+finally block with just an except that closes
old2 = '''        except Exception as e:
            logger.error(f"upsert error: {_safe_str(e)}")
        finally:
            try:
                conn.close()
            except:
                pass'''

new2 = '''        except Exception as e:
            logger.error(f"upsert error: {_safe_str(e)}")
            try:
                conn.close()
            except:
                pass
        else:
            conn.close()'''

# Actually, simpler: just use try/finally without except
old3 = '''        except Exception as e:
            logger.error(f"upsert error: {_safe_str(e)}")
        finally:
            try:
                conn.close()
            except:
                pass'''

new3 = '''        except Exception as e:
            logger.error(f"upsert error: {_safe_str(e)}")
        conn.close()'''

content = content.replace(old3, new3, 1)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

try:
    ast.parse(content)
    print('Syntax OK!')
except SyntaxError as e:
    print(f'SyntaxError line {e.lineno}: {e.msg}')
