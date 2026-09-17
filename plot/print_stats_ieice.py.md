(greefb means gree with fallback)

## 4.1 Experiemtal Setup

### Benchmarks.

total: 693 instances, drawn from 519 graphs

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

## 4.2 Input Graphs and Widths of the Three Decompositions

opt was obtained for 226 graphs, 279 instances

**table 1**:

all graphs

| \|V\|    |   #graphs |   #inst. |
|:---------|----------:|---------:|
| ≤50      |        40 |       52 |
| 51–100   |        58 |       84 |
| 101–200  |       100 |      117 |
| 201–500  |       219 |      256 |
| 501–1000 |        49 |       68 |
| >1000    |        53 |      116 |

opt-available graphs

| \|V\|    |   #graphs |   #inst. | pw(G) min   | pw(G) max   | pw(G) median   |
|:---------|----------:|---------:|:------------|:------------|:---------------|
| ≤50      |        40 |       52 | 1           | 35          | 8.0            |
| 51–100   |        51 |       77 | 4           | 72          | 13.0           |
| 101–200  |        50 |       59 | 4           | 119         | 10.0           |
| 201–500  |        65 |       69 | 4           | 492         | 10.0           |
| 501–1000 |        20 |       22 | 11          | 990         | 17.0           |
| >1000    |         0 |        0 | <NA>        | <NA>        | <NA>           |

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

median width on opt-available:

|           |   0 |
|:----------|----:|
| pw_opt    |  10 |
| pw_orig   |  32 |
| pw_greefb |  11 |

opt width == gree width for 166 graphs

on opt-available graphs:

|        |   wallclock_time_gree_preprocess |   wallclock_time_opt_preprocess |
|:-------|---------------------------------:|--------------------------------:|
| median |                             1.86 |                           2.415 |
| max    |                            12.67 |                        1541.13  |

84.1% finish within 10 sec

opt not computed: 293 graphs, 414 instances

**table 2**:

opt-available:

|           |   0.5 |   0.25 |   0.75 |
|:----------|------:|-------:|-------:|
| pw_orig   |    32 |     11 |  233.8 |
| pw_greefb |    11 |      9 |   17   |
| pw_opt    |    10 |      6 |   17   |

opt-missing:

|           | 0.5   | 0.25   | 0.75   |
|:----------|:------|:-------|:-------|
| pw_orig   | 198.0 | 118.0  | 292.0  |
| pw_greefb | 108.0 | 63.8   | 156.5  |
| pw_opt    | <NA>  | <NA>   | <NA>   |

- on opt-available graphs, gree width ≤ 20: 191 graphs
- on opt-missing graphs, gree width ≤ 20: 9 graphs

## 4.3 Solved Instances

**table 3**:

```
opt_available? opt-available          opt-missing         
problem             shortest farthest    shortest farthest
variable                                                  
orig                     210      208           7        7
greefb                   216      215          17       16
opt                      218      218           0        0
```

percentages:

```
opt_available? opt-available          opt-missing         
problem             shortest farthest    shortest farthest
variable                                                  
orig                    75.3     74.6         1.7      1.7
greefb                  77.4     77.1         4.1      3.9
opt                     78.1     78.1         0.0      0.0
```

### Effects of choosing decompositions.

the solved sets are nested:

on opt-available instances:
- _every instance solved under orig is also solved under gree_
  - conversely, the number of instances solved in orig but not gree is 0 for shortest, and 0 for farthest
- _every instance solved under gree is also solved under opt_
  - conversely, the number of instances solved in gree but not opt is 0 for shortest, and 0 for farthest

on opt-missing instances:
- _every instance solved under orig is also solved under gree_
  - conversely, the number of instances solved in orig but not gree is 0 for shortest, and 0 for farthest
- (opt is not obtained)

### Nesting across variants.

- 'every instance solved on the farthest variant is also solved on the shortest one'
  - conversely, the number of instances solved on farthest but not shortest is 0 in orig, 0 in gree, and 0 in opt

### Width for the flipped instances.

**table 4**:

| graph_name                  |   \|V\| |   \|E\| |   orig |   gree |   opt |   #flip | solved by   |
|:----------------------------|--------:|--------:|-------:|-------:|------:|--------:|:------------|
| games120                    |     120 |     638 |     91 |     46 |    32 |       2 | opt         |
| queen8_12                   |      96 |    1368 |     85 |     68 |    65 |       2 | gree, opt   |
| random_instance006_graph003 |      78 |     234 |     49 |     27 |    23 |       1 | gree, opt   |
| mug88_25                    |      88 |     146 |     32 |     10 |     5 |       1 | gree, opt   |
| mug100_1                    |     100 |     166 |     26 |     16 |     5 |       1 | gree, opt   |

| graph_name                  |   \|V\| |   \|E\| |   orig |   gree | opt   |   #flip | solved by   |
|:----------------------------|--------:|--------:|-------:|-------:|:------|--------:|:------------|
| SAT_exp_instance018         |     270 |     477 |    234 |     23 | <NA>  |       1 | gree        |
| SAT_exp_instance016         |     216 |     376 |    184 |     20 | <NA>  |       1 | gree        |
| SAT_exp_instance014         |     168 |     287 |    140 |     17 | <NA>  |       1 | gree        |
| anna                        |     138 |     493 |     61 |     21 | <NA>  |       2 | gree        |
| random_instance007_graph003 |      91 |     273 |     54 |     31 | <NA>  |       1 | gree        |
| random_instance007_graph005 |      91 |     273 |     53 |     30 | <NA>  |       1 | gree        |
| random_instance006_graph005 |      78 |     234 |     51 |     26 | <NA>  |       1 | gree        |
| ph-05-04                    |     165 |     256 |     43 |     17 | <NA>  |       1 | gree        |

**table 5**:

| graph_name                  |   \|V\| |   \|E\| |   orig |   gree |   opt | shortest solved by   | farthest solved by   |
|:----------------------------|--------:|--------:|-------:|-------:|------:|:---------------------|:---------------------|
| miles500                    |     128 |    1170 |    104 |     30 |    22 | orig, gree, opt      | gree, opt            |
| random_instance005_graph004 |      65 |     195 |     38 |     24 |    20 | orig, gree, opt      | gree, opt            |
| mug100_25                   |     100 |     166 |     32 |     17 |     6 | gree, opt            | opt                  |

| graph_name                  |   \|V\| |   \|E\| |   orig |   gree | opt   | shortest solved by   | farthest solved by   |
|:----------------------------|--------:|--------:|-------:|-------:|:------|:---------------------|:---------------------|
| random_instance007_graph001 |      91 |     273 |     56 |     30 | <NA>  | gree                 | ---                  |

shortest flipped:

| graph_name                  |   #flip |
|:----------------------------|--------:|
| mug100_25                   |       1 |
| random_instance007_graph001 |       1 |

farthest flipped:

| graph_name                  |   #flip |
|:----------------------------|--------:|
| miles500                    |       1 |
| mug100_25                   |       1 |
| random_instance005_graph004 |       1 |

gree solves and orig does not for 16 instances:

- on 10 instances, orig does not finish the first phase within 30 min
- out of them, the minimum time taken for the whole search by gree is 2.49

# 5. Analyses

the range of the size of solution-space ZDD under orig is wide:

|     |   zdd_size_orig |
|:----|----------------:|
| min |               8 |
| max |       142539591 |

## 5.1 The First Phase: Building the Solution-Space ZDD

**table 6**:

```
                         width              |Zsol|                 peak |Zi|            average |Zi|          
                geometric_mean  max geometric_mean        max geometric_mean      max geometric_mean       max
variant  type                                                                                                 
shortest orig             34.5  611         3011.3  142539591         1078.6  1647244          599.1  612349.0
         greefb           12.5  485         1190.8     793894          798.6   391494          457.4  110594.0
         opt              11.7  485          971.0     395153          749.1   278233          433.1   74750.0
farthest orig             34.3  611         2804.8  142539591         1142.0  1658221          570.6  521892.0
         greefb           12.4  485         1156.6     793894          857.2   398418          437.6  146359.0
         opt              11.6  485          947.7     395153          794.7   236594          408.5   73874.0
```
**table 7**:

```
                      zdd_time           wallclock_time              max_memory            
                geometric_mean       max geometric_mean      max geometric_mean         max
variant  type                                                                              
shortest orig            0.183  1497.244          3.043  1711.67        281.948  137248.004
         greefb          0.078  1482.447          1.444  1715.01        170.374  134664.621
         opt             0.072  1459.247          1.283  1706.79        157.658  134662.566
farthest orig            0.159  1475.896          2.937  1629.46        300.098  137247.398
         greefb          0.074  1231.452          1.661  1687.62        183.604  134664.777
         opt             0.069  1229.303          1.457  1683.67        165.270  134663.160
```

Spearman correlation between (width, size):

|    |   Spearman correlation |     p-value |
|---:|-----------------------:|------------:|
|  0 |               0.475391 | 3.07433e-13 |
|  1 |               0.719298 | 9.49679e-35 |
|  2 |               0.699345 | 3.66449e-32 |

opt ZDD size > orig:

- on 37% of the instances
- difference is at most 7% in size, 120 in absolute terms
- at most 2136 nodes under orig

range of the size of ZDD under orig

|     |   zdd_size_orig |
|:----|----------------:|
| min |               8 |
| max |       142539591 |

## 5.2 The Second Phase: Rebuilding the ZDD at Each Step


Spearman correlation between shrink (Zsol, peak Zi):

|    |   Spearman correlation |     p-value |
|---:|-----------------------:|------------:|
|  0 |               0.640642 | 1.17261e-25 |

|                |   ('Zsol', '') |   ('peak Zi', '') |
|:---------------|---------------:|------------------:|
| geometric_mean |        3.10113 |           1.43988 |

second-phase factor ≤ first-phase factor on 80% of the instances

on shrink factor of Zsol ≥ 10, median of shrink factor of max |Zi| is 5.0

Spearman correlation between shrink (peak, average)
shortest: 0.964
farthest: 0.948

### Pronounced examples.

**table 8**:

```
                                              width       Zsol     zdd_time    peak Zi  average Zi  wallclock_time     max_memory
dat_file               vertices edges type                                                                                       
mug88_1_02             88       146   orig       31     893642    14.826937  1412408.0    612349.0     1088.910034   33236.367188
                                      greefb     11       4932     0.016256    36998.0     19022.0           21.77       287.8125
                                      opt         5        455     0.009965     5021.0      3317.0            0.38      36.238281
LGC_exp_instance007_01 343      399   orig       86   11862645    97.035866   274572.0     80709.0      951.710022   33054.800781
                                      greefb     13     172186      3.84457    82003.0     47825.0      568.900024    8534.363281
                                      opt      <NA>       <NA>         <NA>        NaN         NaN            <NA>           <NA>
anna_02                138      493   orig       61  240778360  2839.226318  1419984.0    539484.0     3119.659912  147854.199219
                                      greefb     21      11785     2.398439     2427.0      1683.0            2.64     269.289062
                                      opt      <NA>       <NA>         <NA>        NaN         NaN            <NA>           <NA>
```

## 5.3 Reconfiguration Length

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

_no instance of large width reaches such lengths_
- instances of larger widths have reached ℓ ≤ 20

## 5.4 Width and Solvability

shortest:

```
             sum      len      sum      len
width20 width≤20 width≤20 width>20 width>20
|V|                                        
≤100          93       93       32       43
101–200       40       43       18       74
201–500       40       69        5      187
>500           5       20        0      164
```

percentages:

```
width20  width≤20  width>20
|V|                        
≤100          100        74
101–200        93        24
201–500        58         3
>500           25         0
```

farthest is similar to shortest:

```
             sum      len      sum      len
width20 width≤20 width≤20 width>20 width>20
|V|                                        
≤100          92       93       31       43
101–200       40       43       18       74
201–500       40       69        5      187
>500           5       20        0      164
```
