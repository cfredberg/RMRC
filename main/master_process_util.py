import multiprocessing

def create_process(target, args, name):
    process_name = f"{name}_process"
    p = multiprocessing.Process(target=target, args=args, name=process_name)
    p.daemon = True
    p.start()
    print(f"Created Process: {process_name}")
    return p