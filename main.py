'''
操作Ponepklyoch字典数据库的Python脚本
提供增删查改接口
'''

from __future__ import annotations

import ast
import os
import json
import pathlib as plb

CAPITALS = [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['#']


def capital(key: str) -> str:
    _key = key.lower()
    if 'a' <= _key[0] <= 'z':
        return _key[0]
    return '#'


class Word:
    key: str
    meanings: list[str]
    examples: list[str]

    def __init__(self, key: str, meanings: list[str], examples: list[str]) -> None:
        assert key != ''
        self.key = key
        self.meanings = meanings
        self.examples = examples

    @staticmethod
    def key_from_line(line: str) -> str:
        return line[5:-1]

    @staticmethod
    def key_as_line(key: str) -> str:
        assert key != ''
        return f'WORD={key}\n'

    @staticmethod
    def meanings_from_line(line: str) -> list[str]:
        return ast.literal_eval(line[9:-1])

    @staticmethod
    def meanings_as_line(meanings: list[str]) -> str:
        return f'MEANINGS={meanings}\n'

    @staticmethod
    def examples_from_line(line: str) -> list[str]:
        return ast.literal_eval(line[9:-1])

    @staticmethod
    def examples_as_line(examples: list[str]) -> str:
        return f'EXAMPLES={examples}\n'

    @staticmethod
    def word_from_lines(lines: tuple[str, str, str]) -> Word:
        return Word(Word.key_from_line(lines[0]),
                    Word.meanings_from_line(lines[1]),
                    Word.examples_from_line(lines[2]))

    @staticmethod
    def word_as_lines(word: Word) -> tuple[str, str, str]:
        return (Word.key_as_line(word.key),
                Word.meanings_as_line(word.meanings),
                Word.examples_as_line(word.examples))


class Data:
    data_paths: dict[str, plb.Path]
    stat_path: plb.Path
    stat: dict[str, int]

    def __init__(self) -> None:
        # 初始化数据文件夹
        data_dir = plb.Path('./data/')
        if not data_dir.exists():
            data_dir.mkdir()
        # 初始化统计数据
        self.stat = {x: 0 for x in CAPITALS}
        self.stat_path = data_dir.joinpath('stat.txt')
        if not self.stat_path.exists():
            self.stat_path.touch()
            self.__write_stat_file()
        else:
            self.__read_stat_file()
        # 初始化数据文件
        self.data_paths = {}
        for c in CAPITALS:
            data_path = data_dir.joinpath(f'{c}.pnkc')
            if not data_path.exists():
                data_path.touch()
            self.data_paths[c] = data_path

    def __read_stat_file(self) -> None:
        with open(self.stat_path, 'r', encoding='utf-8') as fp:
            self.stat = json.load(fp)

    def __write_stat_file(self) -> None:
        with open(self.stat_path, 'w', encoding='utf-8') as fp:
            json.dump(self.stat, fp, indent=4)

    def __set_stat(self, c: str, num: int) -> None:
        assert c in CAPITALS
        assert num >= 0
        self.stat[c] = num
        self.__write_stat_file()

    def modify_word(self, word: Word) -> None:
        c = capital(word.key)
        data_path = self.data_paths[c]
        tmp_path = data_path.parent.joinpath(f'~{c}.pnkc.tmp')
        with open(data_path, 'r', encoding='utf-8') as fp:
            if self.stat[c] == 0:
                fp.write(''.join(Word.word_as_lines(word)))
                print(f'已添加{word.key}')
                return
            tmp_path.touch()
            insert_flag = True
            with open(tmp_path, 'r+') as tmp_fp:
                write_flag = True  # 应当写入标志
                process_flag = False  # 已处理标志
                for line in fp:
                    if process_flag:
                        tmp_fp.write(line)
                        continue
                    if line.startswith('WORD='):
                        cur_key = Word.key_from_line(line)
                        if cur_key < word.key:
                            tmp_fp.write(line)
                        elif cur_key == word.key:
                            tmp_fp.write(''.join(Word.word_as_lines(word)))
                            write_flag = False
                            insert_flag = False
                        else:
                            if write_flag:  # 插入时write_flag=True, 替换时则write_flag=False
                                tmp_fp.write(''.join(Word.word_as_lines(word)))
                            write_flag = True
                            process_flag = True
                            tmp_fp.write(line)
                    elif write_flag:
                        tmp_fp.write(line)
                if not process_flag:  # 末尾插入
                    tmp_fp.write(''.join(Word.word_as_lines(word)))
        os.replace(tmp_path, data_path)
        if insert_flag:
            self.__set_stat(c, self.stat[c] + 1)
            print(f'已添加{word.key}')
        else:
            print(f'已修改{word.key}')

    def delete_word(self, key: str) -> None:
        assert key
        c = capital(key)
        if self.stat[c] == 0:
            return
        data_path = self.data_paths[c]
        tmp_path = data_path.parent.joinpath(f'~{c}.pnkc.tmp')
        exist_flag = False
        with open(data_path, 'r', encoding='utf-8') as fp:
            tmp_path.touch()
            with open(tmp_path, 'r+') as tmp_fp:
                write_flag = True  # 应当写入标志
                process_flag = False  # 已处理标志
                for line in fp:
                    if process_flag:
                        tmp_fp.write(line)
                        continue
                    if line.startswith('WORD='):
                        cur_key = Word.key_from_line(line)
                        if cur_key == key:
                            write_flag = False
                            exist_flag = True
                        elif cur_key > key:
                            write_flag = True
                            process_flag = True
                            tmp_fp.write(line)
                        else:
                            tmp_fp.write(line)
                    elif write_flag:
                        tmp_fp.write(line)
        os.replace(tmp_path, data_path)
        if exist_flag:
            self.__set_stat(c, self.stat[c] - 1)
            print(f'已删除{key}')
        else:
            print(f'{key}不存在，没有更改')

    def search_word(self, key: str) -> Word:
        assert key
        c = capital(key)
        if self.stat[c] == 0:
            raise KeyError(f'{key}不存在！')
        data_path = self.data_paths[c]
        with open(data_path, 'r', encoding='utf-8') as fp:
            word_lines = []
            find_flag = False
            for line in fp:
                if line.startswith('WORD='):
                    if Word.key_from_line(line) == key:
                        find_flag = True
                        word_lines.append(line)
                elif find_flag:
                    word_lines.append(line)
                    if line.startswith('EXAMPLES='):
                        break
            if find_flag:
                print(f'已找到{key}')
                return Word.word_from_lines(word_lines)
            print(f'未找到{key}')


if __name__ == '__main__':
    data = Data()
