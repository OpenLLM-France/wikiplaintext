`This is the markdown version of `[`https://fr.wikipedia.org/wiki/Racine_carrée`](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e)

`Plaintext version:..............`[`11817_Racine_carrée.txt`](../wikipedia_html_cleaned/11817_Racine_carrée.txt)

`Original HTML version:..........`[`11817_Racine_carrée.html`](../wikipedia_html/11817_Racine_carrée.html)


[Racine carrée](#racine-carrée)
* [Histoire](#histoire)
* [Construction géométrique de la racine carrée](#construction-géométrique-de-la-racine-carrée)
* [Fonction réelle](#fonction-réelle)
* [Extraction de racines carrées](#extraction-de-racines-carrées)
* [Racines carrées particulières](#racines-carrées-particulières)
   * [Nombre d'or](#nombre-dor)
   * [Nombres entiers supérieurs à 1 sous forme de racines carrées](#nombres-entiers-supérieurs-à-1-sous-forme-de-racines-carrées)
   * [Pi](#pi)
* [Notion algébrique générale](#notion-algébrique-générale)
   * [Définition algébrique d'une racine carrée](#définition-algébrique-dune-racine-carrée)
   * [Racines carrées de nombres complexes](#racines-carrées-de-nombres-complexes)
   * [Racines carrées de matrices et d’opérateurs](#racines-carrées-de-matrices-et-dopérateurs)
---
# [Racine carrée](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e)

En mathématiques élémentaires, la racine carrée d'un nombre réel positif x est l'unique réel positif qui, lorsqu'il est multiplié par lui-même, donne x, c'est-à-dire le nombre positif dont le carré vaut x. On le note √x ou x$^{1/2}$. Dans cette expression, x est appelé le radicande et le signe ${\sqrt {\quad }}$ est appelé le radical. La fonction qui, à tout réel positif, associe sa racine carrée s'appelle la fonction racine carrée.

En algèbre et analyse, dans un anneau ou un corps A, on appelle racine carrée de a tout élément de A dont le carré vaut a. Par exemple, dans le corps des complexes ℂ, on dira de i (ou de − i) qu'il est une racine carrée de − 1. Selon la nature de l'anneau et la valeur de a, on peut trouver 0, 1, 2 ou plus de 2 racines carrées de a.

La recherche de la racine carrée d'un nombre, ou extraction de la racine carrée, donne lieu à de nombreux algorithmes. La nature de la racine carrée d'un entier naturel qui n'est pas le carré d'un entier est à l'origine de la première prise de conscience de l'existence de nombres irrationnels. La recherche de racines carrées pour des nombres négatifs a conduit à l'invention des nombres complexes.

## [Histoire](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Histoire)

La plus ancienne racine carrée connue apparaît vers 1700 av. J.-C. sur la tablette YBC 7289. Il s'agit de la représentation d'un carré avec, sur un côté, le nombre 30 et, le long de la diagonale, une valeur approchée de √2.

## [Construction géométrique de la racine carrée](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Construction_g%C3%A9om%C3%A9trique_de_la_racine_carr%C3%A9e)

La construction géométrique suivante se réalise à la règle et au compas et permet, étant donné un segment OB de longueur a et un segment de longueur 1, de construire un segment de longueur √a :

* construire le segment [AB] de longueur 1 + a et contenant le point O avec AO = 1 ;
* construire le cercle c de diamètre [AB] ;
* construire la droite d perpendiculaire à (OB) et passant par O ;
* nommer H le point d’intersection du cercle c et de la droite d.

Le segment [OH] est de longueur √a.

La preuve consiste à remarquer que les triangles OAH et OHB sont semblables, d'où l'on déduit que OH$^2$ = AO × OB = a, et donc OH = √a.

Cette construction montre que la racine carrée d'un nombre constructible (par exemple un nombre rationnel positif) est encore un nombre constructible.

## [Fonction réelle](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Fonction_r%C3%A9elle)

L’application $x\mapsto x^{2}$ est une bijection de ℝ+ sur ℝ+ dont la réciproque est notée $x\mapsto {\sqrt {x}}$. Cette fonction s’appelle la fonction racine carrée. Géométriquement, on peut affirmer que la racine carrée de l’aire d’un carré du plan euclidien est la longueur de l'un de ses côtés.

La fonction racine carrée vérifie les propriétés élémentaires suivantes valables pour tous nombres réels positifs x et y :

    ${\sqrt {x}}=x^{\frac {1}{2}}$
    ${\sqrt {x\times y}}={\sqrt {x}}\times {\sqrt {y}}$
    ${\sqrt {\frac {x}{y}}}={\frac {\sqrt {x}}{\sqrt {y}}}$ (sous la condition y > 0)
    ${\sqrt {x^{2}}}=|x|$.
* Elle est strictement croissante, comme réciproque d'une bijection croissante sur ℝ+.
* Elle est 1/2-höldérienne donc uniformément continue.
* Elle est dérivable en tout réel strictement positif x, mais elle n’est pas dérivable en x = 0. En ce point, la courbe représentative admet une demi-tangente verticale. Sa fonction dérivée est donnée par :

    ${\frac {\mathrm {d} }{\mathrm {d} x}}{\sqrt {x}}={1 \over 2{\sqrt {x}}}$.
* Elle est de classe C$^∞$ sur ℝ+* :$\forall n\in \mathbb {N} \quad {\frac {\mathrm {d} ^{n}}{\mathrm {d} x^{n}}}{\sqrt {x}}={(-1)}^{n+1}{(2n)! \over n!2^{2n}(2n-1)}{\frac {1}{x^{n-1/2}}}.$
* Son développement en série de Taylor au point 1 est donc, pour tout réel h tel que |h| ≤ 1 :${\sqrt {1-h}}=1-\sum _{n=1}^{\infty }a_{n}h^{n}{\text{ avec }}a_{n}={(2n)! \over (n!)^{2}2^{2n}(2n-1)}>0,$avec convergence normale sur [–1, 1] (voir le § « Développement en série entière » de l'article « Racine d'un nombre »). Les coefficients s'expriment comme quotients de nombres de Catalan par des puissances de 2 :$a_{n}={\frac {C_{n-1}}{2^{2n-1}}}.$Les premières valeurs sont$a_{1}={\frac {1}{2}},a_{2}={\frac {1}{8}},a_{3}={\frac {1}{16}},a_{4}={\frac {5}{128}}.$

## [Extraction de racines carrées](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Extraction_de_racines_carr%C3%A9es)

Le calcul de la racine carré d'un nombre positif n'est pas toujours évident, notamment pour de grands nombres. Ainsi, plusieurs algorithmes ont été développés au cours de l'histoire afin d'obtenir ce nombre. Parmi les méthodes d'extraction de racine carrée, on peut citer notamment la méthode de Héron, qui est une méthode historique qui peut être vue d'un point de vue moderne comme un cas particulier de la méthode de Newton. D'autres méthodes sont basées sur des suites adjacentes, sur des fractions continues ou sur un principe de dichotomie.

## [Racines carrées particulières](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Racines_carr%C3%A9es_particuli%C3%A8res)

### [Nombre d'or](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Nombre_d%27or)

Si p est un nombre réel strictement positif,

    ${\sqrt {p+{\sqrt {p+{\sqrt {p+{\sqrt {p+\cdots }}}}}}}}={\frac {1+{\sqrt {4p+1}}}{2}}$.

Pour p = 1, on obtient le nombre d'or :

    $\varphi ={\sqrt {1+{\sqrt {1+{\sqrt {1+{\sqrt {1+\cdots }}}}}}}}$.

### [Nombres entiers supérieurs à 1 sous forme de racines carrées](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Nombres_entiers_sup%C3%A9rieurs_%C3%A0_1_sous_forme_de_racines_carr%C3%A9es)

Ramanujan a découvert les formules suivantes :

    ${\sqrt {1+2{\sqrt {1+3{\sqrt {1+\dots }}}}}}=3$ et ${\sqrt {6+2{\sqrt {7+3{\sqrt {8+\dots }}}}}}=4$.

Ces formules se généralisent, ce qui donne en particulier, pour tout réel $n\geq 0$ :

    $n+2={\sqrt {1+(n+1){\sqrt {1+(n+2){\sqrt {1+(n+3){\sqrt {\dots }}}}}}}}$ et $n+3={\sqrt {n+5+(n+1){\sqrt {n+6+(n+2){\sqrt {n+7+\dots }}}}}}$.

### [Pi](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Pi)

Le nombre π s’exprime sous la forme d’une itération infinie de racines carrées :

    $\pi =\lim _{k\to \infty }\left(2^{k}\cdot {\sqrt {2-{\sqrt {2+{\sqrt {2+{\sqrt {2+\cdots {\sqrt {2+{\sqrt {2}}}}}}}}}}}}\right)$ , où k est le nombre de racines carrées emboitées

Ou encore :

    $\pi =\lim _{k\to \infty }\left(3\cdot 2^{k-1}\cdot {\sqrt {2-{\sqrt {2+{\sqrt {2+{\sqrt {2+\cdots {\sqrt {2+{\sqrt {2+{\sqrt {3}}}}}}}}}}}}}}\right)$

(formules qui se démontrent par calcul trigonométrique direct : le terme de droite de la première, par exemple, vaut $2^{k}\sin(\pi /2^{k})$).

## [Notion algébrique générale](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Notion_alg%C3%A9brique_g%C3%A9n%C3%A9rale)

### [Définition algébrique d'une racine carrée](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#D%C3%A9finition_alg%C3%A9brique_d%27une_racine_carr%C3%A9e)

Soient x et a deux éléments d’un anneau A, tels que x$^2$ = a. L'élément x est alors une racine carrée de a. La notation √a est néanmoins souvent déconseillée car il peut exister plusieurs tels éléments x.

En général (si l'anneau n'est pas intègre ou s'il n'est pas commutatif), un élément peut avoir plus de deux racines carrées. Par exemple dans l'anneau ℤ/9ℤ, les racines carrées de 0 sont 0, 3 et -3, et dans le corps gauche des quaternions, tout réel strictement négatif possède une infinité de racines carrées.

Dans le cas des nombres réels, un auteur parlant d'une racine carrée de 2, traite d'un des deux éléments √2 ou bien -√2. En revanche, l'expression la racine carrée de deux évoque toujours la solution positive. Comme l'expression √2 est toujours positive et le terme fonction racine définie sur les réels positifs désigne toujours la valeur positive, on évite cette confusion dans les enseignements un peu élémentaires des mathématiques en ne faisant usage que de l'expression : la racine carrée, alors toujours positive.

### [Racines carrées de nombres complexes](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Racines_carr%C3%A9es_de_nombres_complexes)

La racine carrée sur ℝ est définie seulement pour les nombres positifs. Dans la résolution effective des équations polynomiales, l’introduction d’une racine carrée formelle d’un nombre négatif dans les calculs intermédiaires donne des résultats exacts. C’est ainsi que le corps des nombres complexes a été introduit

   Pour tout nombre complexe non nul z = a + ib (avec a et b réels), il existe exactement deux nombres complexes w tels que w$^2$ = z. Ils sont opposés l'un de l'autre.
   * Si b est non nul, ils sont donnés par :

       $w=\pm \left({\sqrt {\frac {{\sqrt {a^{2}+b^{2}}}+a}{2}}}+\mathrm {i} \ \operatorname {signe} (b){\sqrt {\frac {{\sqrt {a^{2}+b^{2}}}-a}{2}}}\right)$, avec $\operatorname {signe} (b)={\frac {b}{|b|}}$.
   * Si b est nul et a est négatif, cette formule se simplifie en :

       $w=\pm \mathrm {i} {\sqrt {|a|}}$.
   * Par ailleurs, si z n'est pas un réel négatif (c.-à-d. si b est non nul ou si a est positif),

       $w=\pm {\frac {z+|z|}{\sqrt {2(a+|z|)}}}$.

Pour trouver w = x + iy tel que w$^2$ = a + ib, on pose le système suivant :

    ${\begin{cases}w^{2}=z\\|w|^{2}=|z|\end{cases}}$
    ${\begin{cases}(x+\mathrm {i} y)^{2}=a+\mathrm {i} b\\x^{2}+y^{2}={\sqrt {a^{2}+b^{2}}}\end{cases}}$
    ${\begin{cases}x^{2}-y^{2}+\mathrm {i} 2xy=a+\mathrm {i} b\\x^{2}+y^{2}={\sqrt {a^{2}+b^{2}}}\end{cases}}$

Par identification de la partie réelle et imaginaire, on obtient :

    ${\begin{cases}x^{2}-y^{2}=a\\2xy=b\\x^{2}+y^{2}={\sqrt {a^{2}+b^{2}}}.\end{cases}}$

On en déduit alors x$^2$ et y$^2$ en ajoutant et soustrayant les première et troisième équations. Le signe du produit xy est celui de b, d'où la première expression des deux couples de solutions pour x et y.

Mais une manière moins traditionnelle de résoudre ce système est de faire dans un premier temps seulement la somme (des première et troisième équations) :

    $2x=\pm {\sqrt {2(a+|z|)}}$,

ce qui, si z n'est pas un réel négatif, mène à la dernière formule.

Les deux racines carrées de i sont

    1 + i/√2 = $\mathrm {e} ^{\frac {\mathrm {i} \pi }{4}}=\cos {\frac {\pi }{4}}+\mathrm {i} \sin {\frac {\pi }{4}}$ ≈ 0,707 + 0,707 i

et son opposé.

Pour des raisons de nature topologique, il est impossible de prolonger la fonction racine carrée, de ℝ+ dans ℝ+, en une fonction continue $f:\mathbb {C} \rightarrow \mathbb {C}$ vérifiant f(z)$^2$ = z.

On appelle détermination de la racine carrée sur un ouvert U de ℂ toute fonction continue $f:U\rightarrow \mathbb {C}$ vérifiant $f(z)^{2}=z$.

La détermination principale de la racine carrée est la fonction de ℂ dans ℂ ainsi définie : si z s’écrit sous forme trigonométrique z = r e$^{iφ}$ avec –π < φ ≤ π, alors on pose f(z) = √r e$^{iφ/2}$. Cette détermination principale n’est continue en aucun point de la demi-droite des réels strictement négatifs, et est holomorphe sur son complémentaire.

Quand le nombre est dans sa forme algébrique z = a + ib, cette définition se traduit par :

    $f(a+ib)={\sqrt {\frac {\left|a+\mathrm {i} b\right|+a}{2}}}\pm \mathrm {i} {\sqrt {\frac {\left|a+\mathrm {i} b\right|-a}{2}}}$

où le signe de la partie imaginaire de la racine est

* si b ≠ 0 : le signe de b
* si b = 0 et a < 0 : le signe +
* si b = 0 et a ≥ 0 : pas de signe (le nombre est nul).

Notons qu’à cause de la nature discontinue de la détermination principale de la racine carrée dans le plan complexe, la relation ${\sqrt {zz'}}={\sqrt {z}}{\sqrt {z'}}$ devient fausse en général.

### [Racines carrées de matrices et d’opérateurs](https://fr.wikipedia.org/wiki/Racine_carr%C3%A9e#Racines_carr%C3%A9es_de_matrices_et_d%E2%80%99op%C3%A9rateurs)

Si A est une matrice autoadjointe positive ou un opérateur autoadjoint positif en dimension finie, alors il existe exactement une matrice autoadjointe positive ou un opérateur autoadjoint positif B tel que B$^2$ = A. On pose alors : √A = B.

Plus généralement, pour toute matrice normale ou tout opérateur normal en dimension finie A, il existe des opérateurs normaux B tels que B$^2$ = A. Cette propriété se généralise à tout opérateur borné normal sur un espace de Hilbert.

En général, il y a plusieurs tels opérateurs B pour chaque A et la fonction racine carrée ne peut pas être définie pour les opérateurs normaux d’une façon satisfaisante (continue par exemple). Les opérateurs positifs sont apparentés à des nombres réels positifs, et les opérateurs normaux sont apparentés à des nombres complexes. Les articles sur la théorie des opérateurs développent davantage ces aspects.

