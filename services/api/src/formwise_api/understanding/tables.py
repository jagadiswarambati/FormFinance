from formwise_api.understanding.models import StructuredSection, StructuredTable


class DelimitedTableExtractor:
    def extract(self, text: str, sections: list[StructuredSection]) -> list[StructuredTable]:
        tables: list[StructuredTable] = []
        lines = text.splitlines()
        index = 0
        while index < len(lines):
            delimiter = "|" if lines[index].count("|") >= 2 else "\t" if lines[index].count("\t") >= 1 else None
            if delimiter is None:
                index += 1
                continue
            group: list[list[str]] = []
            while index < len(lines) and delimiter in lines[index]:
                row = [cell.strip() for cell in lines[index].strip().strip("|").strip().split(delimiter)]
                if len(row) > 1:
                    group.append(row)
                index += 1
            if len(group) >= 2:
                tables.append(StructuredTable(id=f"table-{len(tables) + 1}", headers=group[0], rows=group[1:], confidence=0.8))
        return tables
