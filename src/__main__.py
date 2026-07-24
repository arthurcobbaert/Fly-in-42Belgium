from src.parser.parsing import map_picker, Parser
import sys

def main():
    args = map_picker()
    parse = Parser()
    data: list[str] = []
    try:
        with open(args.input) as f:
            for l in f:
                if not l:
                    continue
                data.append(l)
    except (FileNotFoundError, PermissionError) as e:
        sys.exit(e)
    try:
        parse.parse_lines(data)
    except Exception as e:
        sys.exit(e)



if __name__ == "__main__":
    main()
