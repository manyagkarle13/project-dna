from chat.static_analysis import run_static_analysis

def test_ast():
    code = """
def bad_func(my_list=[]):
    try:
        print("hello")
    except:
        pass
"""
    findings = run_static_analysis("test.py", code)
    print("Findings:")
    for f in findings:
        print(f)
        
if __name__ == "__main__":
    test_ast()
