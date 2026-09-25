(greefb means gree with fallback)

# IV. Experimental Results
## A. Experimental Setup
### a) Benchmarks

total: 693 instances, drawn from 519 graphs
- 693 instances for farthest as well

|        |   vertices |
|:-------|-----------:|
| min    |          6 |
| max    |      40000 |
| median |        274 |

|        |          edges |
|:-------|---------------:|
| min    |    5           |
| max    |    1.32534e+07 |
| median | 1014           |

## B. Input Graphs and Widths of the Three Decompositions

opt was obtained for 226 graphs, 279 instances

**table I**:

| \|V\|    |   #graphs |   #inst. |   \|E\| min |   \|E\| max |   pw(G) min |   pw(G) max |   pw(G) median |
|:---------|----------:|---------:|------------:|------------:|------------:|------------:|---------------:|
| ≤50      |        40 |       52 |           5 |         476 |           1 |          35 |              8 |
| 51–100   |        51 |       77 |          78 |        1470 |           4 |          72 |             13 |
| 101–200  |        50 |       59 |         144 |        6961 |           4 |         119 |             10 |
| 201–500  |        65 |       69 |         300 |      121275 |           4 |         492 |             10 |
| 501–1000 |        20 |       22 |        1835 |      449449 |          11 |         990 |             17 |

gree is computed on 518 graphs

queen200x200:

|                         | 318          |
|:------------------------|:-------------|
| graph_name              | queen200x200 |
| vertices                | 40000        |
| edges                   | 13253400     |
| solved?_gree_preprocess | 0            |

- gree width > orig width for 7 graphs + queen200x200
- the number of instances is 14 + 4 (queen200x200)
  - out of these graphs, opt is available for 3 graphs, 6 instances

(Figure 2 is pw_three_box)

quartiles of widths on opt-available:

|                |   pw_orig |   pw_greefb |   pw_opt |
|:---------------|----------:|------------:|---------:|
| median         |        32 |          11 |       10 |
| lower quartile |        11 |           9 |        6 |
| upper quartile |       234 |          17 |       17 |

opt width == gree width for 166 graphs

on opt-available graphs:

|        |   wallclock_time_gree_preprocess |   wallclock_time_opt_preprocess |
|:-------|---------------------------------:|--------------------------------:|
| median |                              1.9 |                             2.4 |
| max    |                             12.7 |                          1541.1 |

84% finish within 10 sec

opt not computed: 293 graphs, 414 instances

## C. Solved Instances

**table II**:

```
opt_available? opt-available             opt-missing           
variable                orig greefb  opt        orig greefb opt
problem                                                        
shortest                 210    216  218           7     17   0
farthest                 208    215  218           7     16   0
```

the solved sets are nested:

### a) opt-available instances:

- _every instance solved under orig is also solved under gree_
  - conversely, the number of instances solved in orig but not gree is 0 for shortest, and 0 for farthest
- _every instance solved under gree is also solved under opt_
  - conversely, the number of instances solved in gree but not opt is 0 for shortest, and 0 for farthest

### b) on opt-missing instances:

- _every instance solved under orig is also solved under gree_
  - conversely, the number of instances solved in orig but not gree is 0 for shortest, and 0 for farthest

### c) Nesting across variants:

- _every instance solved on the farthest variant is also solved on the shortest one_
  - conversely, the number of instances solved on farthest but not shortest is 0 in orig, 0 in gree, and 0 in opt

### d) Width for the flipped instances

13 graphs, 5 of them opt-available, 16 instances

|           |   min |   max |   median |
|:----------|------:|------:|---------:|
| pw_orig   |    26 |   234 |       54 |
| pw_greefb |    10 |    68 |       23 |

# V. Analyses

the range of the size of solution-space ZDD under orig is wide:

|     |   zdd_size_orig |
|:----|----------------:|
| min |               8 |
| max |       142539591 |

## A. The First Phase: Building the Solution-Space ZDD

**table III**:

```
                            pw              zdd_size                    zdd_time         wallclock_time             max_memory          
                geometric_mean    max geometric_mean          max geometric_mean     max geometric_mean     max geometric_mean       max
variant  type                                                                                                                           
shortest orig             34.5  611.0         3011.0  142539591.0          0.183  1497.2           3.04  1711.7          282.0  137248.0
         greefb           12.5  485.0         1191.0     793894.0          0.078  1482.4           1.44  1715.0          170.0  134665.0
         opt              11.7  485.0          971.0     395153.0          0.072  1459.2           1.28  1706.8          158.0  134663.0
farthest orig             34.3  611.0         2805.0  142539591.0          0.159  1475.9           2.94  1629.5          300.0  137247.0
         greefb           12.4  485.0         1157.0     793894.0          0.074  1231.5           1.66  1687.6          184.0  134665.0
         opt              11.6  485.0          948.0     395153.0          0.069  1229.3           1.46  1683.7          165.0  134663.0
```

Spearman correlation between (width, size):

|        |   Spearman correlation |     p-value |
|:-------|-----------------------:|------------:|
| orig   |                   0.48 | 3.07433e-13 |
| greefb |                   0.72 | 9.49679e-35 |
| opt    |                   0.7  | 3.66449e-32 |

opt ZDD size > orig:

- on 37% of the instances
- difference is at most 7% in size, 120 in absolute terms
- at most 2136 nodes under orig

## B. The Second Phase: Rebuilding the ZDD at Each Step

Spearman correlation between shrink (Zsol, peak Zi):

|    |   Spearman correlation |     p-value |
|---:|-----------------------:|------------:|
|  0 |                   0.64 | 1.17261e-25 |

|                |   ('Zsol', '') |   ('peak Zi', '') |
|:---------------|---------------:|------------------:|
| geometric_mean |            3.1 |               1.4 |

second-phase factor ≤ first-phase factor on 80% of the instances

on shrink factor of Zsol ≥ 10, median of shrink factor of max |Zi| is 5.0

| dat_file   |   vertices |   edges |   pw_orig |   pw_greefb |   pw_opt |
|:-----------|-----------:|--------:|----------:|------------:|---------:|
| mug88_1_02 |         88 |     146 |        31 |          11 |        5 |

| type   |   zdd_nodes_peak |
|:-------|-----------------:|
| opt    |             5021 |
| greefb |            36998 |
| orig   |          1412408 |

# C. Reconfiguration Length

range of ℓ, shortest

|     |   reconfiguration_sequence_length |
|:----|----------------------------------:|
| min |                                 1 |
| max |                            221003 |

width of ℓ ≥ 100, shortest

|        |   pw_greefb |
|:-------|------------:|
| max    |          23 |
| median |          10 |

ℓ < 100

|        |   pw_greefb |
|:-------|------------:|
| max    |         485 |
| median |          17 |
