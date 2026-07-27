from src.parser.parsing import map_picker, Parser
import sys

def main():
    args = map_picker()
    parse = Parser()
    data: list[str] = []
    valid_lines: list[str] = []
    try:
        with open(args.input) as f:
            for l in f:
                if not l:
                    continue
                data.append(l)
    except (FileNotFoundError, PermissionError) as e:
        sys.exit(e)
    try:
        valid_lines = parse.parse_lines(data)
        print(parse.parse_data(valid_lines))
    except Exception as e:
        sys.exit(e)



if __name__ == "__main__":
    main()
