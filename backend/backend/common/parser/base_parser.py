from . import utils_md as tools_md


class BaseParser:
    def __init__(self, data, with_parse=True, debug=False, **kwargs):
        self.fm = None
        self.data = data
        if with_parse:
            self.root_block = self.parse(self.data, debug=debug)

    def parse(self, data, debug=False):
        print("BaseParser.parse() is not implemented")
        return None

    def get_blocks(self, with_toc=False):
        if self.root_block is None:
            return []
        return self.root_block.get_blocks(with_toc=with_toc)

    def dump(self, show_content=False):
        print(f"total blocks: {len(self.root_block.get_blocks())}")
        if self.root_block is not None:
            self.root_block.dump(show_content=show_content)

    def dump_toc(self):
        print(f"total blocks: {len(self.root_block.get_blocks())}")
        if self.root_block is not None:
            self.root_block.dump_toc()

    def save(self, path):
        data = self.root_block.to_md()
        with open(path, "w", errors="ignore") as fp:
            if self.fm is not None:
                tools_md.write_front_matter(fp, self.fm)
            fp.write(data)
            fp.close()

    def get_meta_info(self):
        return None
