import ast

class BottleneckCounter(ast.NodeVisitor):
    def __init__(self):
        self.memory_calls = 0
        self.cpu_calls = 0
        self.gpu_draw_calls = 0
        self.max_int = 2**31 - 1
        self.in_loop = 0
        self.counts = []

    def visit_Call(self, node):
        self.cpu_calls += 1
        self.generic_visit(node)

    def visit_Name(self, node):
        self.memory_calls += 1

    def visit_Attribute(self, node):
        if node.attr.startswith('render'):
            self.gpu_draw_calls += 1 * self.in_loop
        self.generic_visit(node)

    def visit_For(self, node):
        self.in_loop += 1
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
            if isinstance(node.iter.args[0], ast.Num):
                self.cpu_calls += node.iter.args[0].n
        else:
            self.cpu_calls += 1
        self.memory_calls += 1
        self.generic_visit(node)
        self.in_loop -= 1
        self.counts.append((node.lineno, node.end_lineno, self.memory_calls, self.cpu_calls, self.gpu_draw_calls))

    def visit_While(self, node):
        self.in_loop += 1
        if not any(isinstance(child, ast.Break) or isinstance(child, ast.Return) for child in ast.walk(node)):
            self.cpu_calls += self.max_int
        else:
            self.cpu_calls += 1
        self.memory_calls += 1
        self.generic_visit(node)
        self.in_loop -= 1
        self.counts.append((node.lineno, node.end_lineno, self.memory_calls, self.cpu_calls, self.gpu_draw_calls))

    def visit_FunctionDef(self, node):
        self.cpu_calls += 1
        self.memory_calls += 1
        self.generic_visit(node)
        self.counts.append((node.lineno, node.end_lineno, self.memory_calls, self.cpu_calls, self.gpu_draw_calls))

    def visit_BinOp(self, node):
        self.cpu_calls += 1
        self.generic_visit(node)

def count_bottlenecks(code):
    tree = ast.parse(code)
    counter = BottleneckCounter()
    counter.visit(tree)
    return counter.counts

def main():
    with open('test.py', 'r') as f:
        code = f.read()
    counts = count_bottlenecks(code)
    for i, (start_line, end_line, memory_calls, cpu_calls, gpu_draw_calls) in enumerate(counts):
        print(f"Operable collection-span {i+1} (Lines {start_line}-{end_line}):")
        print(f"\tMemory calls: {memory_calls}")
        print(f"\tCPU calls: {cpu_calls}")
        print(f"\tGPU draw calls: {gpu_draw_calls}")

if __name__ == "__main__":
    main()
