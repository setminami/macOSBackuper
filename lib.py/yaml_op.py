# TokageUtilから一部抽出 yaml特殊設定のみ一般化すべき
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

def readYamlSetting(seed:str):
    """ 
    各YAML設定ファイルもしくはYAML文字列を読み込み
    この関数以外から個別に読み込まないこと 

    e.g., 
    somedict = fileutil.readYamlSetting('../settings/rpc.yml')
    somedict = fileutil.readYamlSetting("{a: 'AAA'}"")  Yaml書式注意  
    @param seed fileの場所かYaml文字列 ファイルが見つからない場合はYaml文字列と推定する
    @return yamlをinstance化して返す
    """
    assert(seed != '')
    get_yml = lambda f: yaml.load(f, Loader=__yaml_loader())

    try:
        # file名優先
        if os.path.isfile(seed):
            import codecs
            with codecs.open(seed, 'r', 'UTF-8') as f:
                yml = get_yml(f)
        else: # fileが存在しなければYaml文字列として処理する
            yml = get_yml(seed)
    except yaml.scanner.MarkedYAMLError as mye:
        print('%s %s\n%s\n%s'%(colored('RED', 'YAML ERROR:'), mye.problem_mark, mye.problem, mye.note))
        sys.exit(1)

    # Debug: print(yml)
    # Memo: PyYaml-3.12時点で確実な方法として採用 Resolverに含めたい
    for k, v in yml.items():
        if isinstance(v, str) and '~/' in v:
            yml[k] = os.path.expanduser(v)
    return yml

def eval_in_yaml(yaml_dict:dict):
    """
    **ハイパーパラメータ設定ファイル内で変数間のrelationを明確かつ動的に設定したい**
    # http://docs.sympy.org/latest/modules/core.html
    同YAML内の変数展開と四則演算 + - * ** / sin(), cos(),級数展開... 対応　-> see sympify() spec
    // はint -> floatなど型変換のため、要文字列parse 見合わせ

    Memo: learningutil.pyで読み込むYamlは継承dict<-list構造を持つが、演算簡素化のため継承展開後の単階層dictを対象とする
    # Refactor: yaml_dict階層深度対応
    
    e.g., 
    yaml中に
    ---
    validation_ratio: 10
    in_top_k: 1
    early_stop_patience: validation_ratio * in_top_k
    x: in_top_k
    y: in_top_k * 5
    ---
    >> early_stop_patience -> 10
    >> x -> 1
    >> y: 5
    とか評価時展開されるやーつ

    caller:
    yml = hypparamを読み込んだ連想配列
    for h in [x for x in yml['hyper_params'] if x['checkout']]:
        h.pop('checkout')
        reduced.append(eval_in_yaml(h))
    
    @param yaml_dict dict化されたYamlインスタンス
    @return 変数展開/演算済みYamlインスタンス
    """
    keys = yaml_dict.keys()
    from sympy import Symbol, sympify
    from sympy.core.sympify import SympifyError
    try:
        symbols = {s:Symbol(s) for s in keys}
        # Contract: 演算式は文字列扱い
        tmp = {k:v for k, v in yaml_dict.items() if isinstance(v, str)}
        for tk, tv in tmp.items():
            vals_dict = {}
            expr = None
            for k in keys:
                if tv.count(k) > 0:
                    # Contract: sympifyがstrip()する前提
                    if expr is None: # 代入式は含まれるkey数分巡ってくる
                        expr = (tk, sympify(tv))
                    vals_dict[symbols[k]] = yaml_dict[k] # Memo: 浮動小数点文字列表現 OK
                    pass
                pass
            # Memo: symbolを含むvalueが少なくとも存在する
            if (expr is not None) and (__is_valid_expr(expr[1].atoms(), set(vals_dict.keys()))):
                yaml_dict[expr[0]] = expr[1].subs(vals_dict)
            pass
    except SympifyError as se:
        print('Invalid Input found. %s'%se.expr)
        sys.exit(1)
    return yaml_dict

def __is_valid_expr(vset:set, vals:list):
    """ 
    exprと、expr.subs()に渡す変数辞書が政党であることを保証したい
    # operate_yamlに内包すると長くなるため外だし
    """
    # vsetは数値も要素に持つ
    assert(len(vals) <= len(vset))
    valset = set(vals)
    from sympy import Symbol
    symbol_only = set([s for s in vset if isinstance(s, Symbol)])
    return (len(valset ^ symbol_only) == 0)

def __yaml_loader():
    """
    as private func
    see also. http://www.yaml.org/refcard.html
              http://pyyaml.org/wiki/PyYAML
    """
    loader = yaml.SafeLoader
    import re
    loader.add_implicit_resolver(
        u'tag:yaml.org,2002:float',
        re.compile(u'''^(?:
         [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
        |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
        |\\.[0-9_]+(?:[eE][-+][0-9]+)?
        |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
        |[-+]?\\.(?:inf|Inf|INF)
        |\\.(?:nan|NaN|NAN))$''', re.X),
        list(u'-+0123456789.'))

    loader.add_implicit_resolver(
        u'tag:yaml.org,2002:bool',
        re.compile(u'''^(?:true|True|TRUE|false|False|FALSE)$''', re.X),
        list(u'tTfF'))

    loader.add_implicit_resolver(
        u'tag:yaml.org,2002:null',
        re.compile(u'''^(?: ~
        |null|Null|NULL
        | )$''', re.X),
        [u'~', u'n', u'N', u''])

    loader.add_implicit_resolver(
        u'tag:yaml.org,2002:timestamp',
        re.compile(u'''^(?:[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]
        |[0-9][0-9][0-9][0-9] -[0-9][0-9]? -[0-9][0-9]?
        (?:[Tt]|[ \\t]+)[0-9][0-9]?
        :[0-9][0-9] :[0-9][0-9] (?:\\.[0-9]*)?
        (?:[ \\t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?)$''', re.X),
        list(u'0123456789'))
    return loader
