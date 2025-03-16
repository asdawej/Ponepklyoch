'''
操作Ponepklyoch字典数据库的Python脚本
提供增删查改接口
'''

from __future__ import annotations

import ast
import json
import os
import pathlib as plb
import sys

import easygui as eg

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
        '''
        将pnkc格式单词数据字符串转化为`Word`类对象

        :param lines: pnkc格式单词数据字符串
        :return: 对应的`Word`类对象
        '''
        return Word(Word.key_from_line(lines[0]),
                    Word.meanings_from_line(lines[1]),
                    Word.examples_from_line(lines[2]))

    @staticmethod
    def word_as_lines(word: Word) -> tuple[str, str, str]:
        '''
        将`Word`类对象转化为pnkc格式单词数据字符串

        :param word: `Word`类对象
        :return: 对应的pnkc格式单词数据字符串
        '''
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
        self.stat = {c: 0 for c in CAPITALS}
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

    def modify_word(self, word: Word) -> bool:
        '''
        修改或加入单词

        :param word: 待修改或加入单词
        :return: 如果是加入新单词返回`True`，否则返回`False`
        '''
        c = capital(word.key)
        data_path = self.data_paths[c]
        tmp_path = data_path.parent.joinpath(f'~{c}.pnkc.tmp')
        with open(data_path, 'r+', encoding='utf-8') as fp:
            if self.stat[c] == 0:
                fp.write(''.join(Word.word_as_lines(word)))
                self.__set_stat(c, 1)
                return True
            tmp_path.touch()
            insert_flag = True
            with open(tmp_path, 'r+', encoding='utf-8') as tmp_fp:
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
        return insert_flag

    def delete_word(self, key: str) -> bool:
        '''
        删除单词

        :param key: 待删除单词
        :return: 原本该单词是否存在
        '''
        assert key
        c = capital(key)
        if self.stat[c] == 0:
            return False
        data_path = self.data_paths[c]
        tmp_path = data_path.parent.joinpath(f'~{c}.pnkc.tmp')
        exist_flag = False
        with open(data_path, 'r', encoding='utf-8') as fp:
            tmp_path.touch()
            with open(tmp_path, 'r+', encoding='utf-8') as tmp_fp:
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
        return exist_flag

    def search_word(self, key: str) -> Word | None:
        '''
        查询单词

        :param key: 待查询单词
        :return: 查询结果
        :return None: 查询失败
        '''
        assert key
        c = capital(key)
        if self.stat[c] == 0:
            return None
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
                return Word.word_from_lines(word_lines)
        return None

    def scan(self) -> dict[str, dict[str, Word]]:
        '''
        扫描所有数据并送入内存

        :return: 包含所有数据的字典
        '''
        ret = {c: {} for c in CAPITALS}
        for c in CAPITALS:
            with open(self.data_paths[c], 'r', encoding='utf-8') as fp:
                word_lines = []
                cur_key = ''
                for line in fp:
                    word_lines.append(line)
                    if line.startswith('WORD='):
                        cur_key = Word.key_from_line(line)
                    elif line.startswith('EXAMPLES='):
                        ret[c][cur_key] = Word.word_from_lines(word_lines)
                        word_lines = []
        return ret


if __name__ == '__main__':
    data = Data()
    data_dict = data.scan()
    GUI_TITLE = 'Ponepklyoch字典'
    while True:
        opt = eg.buttonbox(msg='请选择你需要进行的操作：', title=GUI_TITLE, choices=['修改', '删除', '查询', '退出'])
        match opt:
            case '修改':
                key = eg.enterbox(msg='请输入你需要修改或加入的单词：', title=GUI_TITLE)
                if not key:
                    continue
                c = capital(key)
                try:  # 修改单词
                    word = data_dict[c][key]
                    meanings = eg.textbox(msg='请修改释义：', title=GUI_TITLE, text=word.meanings)
                    if meanings is None:
                        continue
                    examples = eg.textbox(msg='请修改例句：', title=GUI_TITLE, text=word.examples)
                    if examples is None:
                        continue
                    new_word = Word(key, meanings.split('\n'), examples.split('\n'))
                    data_dict[c][key] = new_word
                    data.modify_word(new_word)
                    eg.msgbox(msg=f'已修改{key}', title=GUI_TITLE)
                except KeyError:  # 加入新单词
                    meanings = eg.textbox(msg='请编写释义：', title=GUI_TITLE)
                    if meanings is None:
                        continue
                    examples = eg.textbox(msg='请编写例句：', title=GUI_TITLE)
                    if examples is None:
                        continue
                    new_word = Word(key, meanings.split('\n'), examples.split('\n'))
                    data_dict[c][key] = new_word
                    data.modify_word(new_word)
                    eg.msgbox(msg=f'已增加{key}', title=GUI_TITLE)
            case '删除':
                key = eg.enterbox(msg='请输入你需要删除的单词：', title=GUI_TITLE)
                if not key:
                    continue
                try:
                    del data_dict[capital(key)][key]
                except KeyError:
                    eg.msgbox(msg=f'{key}不存在！', title=GUI_TITLE)
                    continue
                data.delete_word(key)
                eg.msgbox(msg=f'已删除{key}。', title=GUI_TITLE)
            case '查询':
                key = eg.enterbox(msg='请输入你需要查询的单词：', title=GUI_TITLE)
                if not key:
                    continue
                try:
                    word = data_dict[capital(key)][key]
                except KeyError:
                    eg.msgbox(msg=f'未找到{key}！', title=GUI_TITLE)
                    continue
                msg = (f'单词：{word.key}\n'
                       '释义：\n' +
                       ''.join([f'- {s}\n' for s in word.meanings]) +
                       '例句：\n' +
                       ''.join([f'- {s}\n' for s in word.examples]))
                eg.msgbox(msg=msg, title=GUI_TITLE)
            case _:
                sys.exit(0)
