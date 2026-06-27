#lang racket

(require data/gvector
         racket/cmdline)

(require "../util/macros.rkt")

(define indir (make-parameter "../run_pathwidth_opt/output_1h/"))
(define graphs (make-parameter "../2023result/docs/solver/benchmark/"))
(define out (make-parameter "./pw.col/"))
(define mode (make-parameter "opt"))
(define suffix-name (make-parameter ".pw"))

(module+ main
  (command-line
   #:once-each
   ["--indir" path
              "where to find log files from Pathwidth"
              (indir path)]
   ["--graphs" path
               "where to find .col files"
               (graphs path)]
   ["--out" path
            "where to output new .col files"
            (out path)]
   ["--suffix-name" suffix
                    "new files are named <graph-name><suffix>.col"
                    (suffix-name suffix)]
   #:args ()
   (void))
  
  (define cols
    (find-files (λ (p)
                  (path-has-extension? p #".col"))
                (graphs)
                #:follow-links? #t))
  
  (for ([path (in-directory (indir))]
        #:when (path-has-extension? path #".log"))
    (define base
      (--> path
           file-name-from-path
           path->string))
    (define i (string-find base ".col"))
    (define graph-name (substring base 0 i))
    (match-define (list col-path)       ; must find a single file
      (filter (λ (p)
                (--> p
                     (path-replace-extension "")
                     file-name-from-path
                     path->string
                     (string=? graph-name)))
              cols))
    
    (define-values (c p e)
      (col->c/p/e col-path))

    (define-values (solved? v-seq)      ; always last sequence
      (pathwidth-log->solved?/seq path))

    (when solved?
      (write-colfile v-seq
                     c p e
                     (build-path (out)
                                 ;; don't convert . to _
                                 (string-append graph-name (suffix-name) ".col")
                                 ))
      (printf "processed ~a~n" graph-name)))

  (printf "wrote all files to ~a~n" (out)))

(define additional-line "ADDENDUM: reordered according to pathwidth log")

;; e is vector for convenience
(define (col->c/p/e path)
  (define c (make-gvector))
  (define p (make-gvector #:capacity 1))
  (define e #f)
  (define e-n 0)

  (call-with-input-file path
    (λ (in)
      (for ([line (in-lines in)])
        (case (string-ref line 0)
          [(#\c)
           (gvector-add! c (substring line 2))]
          [(#\p)
           (define prob (string-trim (substring line 2)))
           (define size
             (->> (string-find prob " ")
                  add1
                  (substring prob)
                  string->number))
           (set! e (make-vector size))
           (gvector-add! p prob)]
          [(#\e)                        ; comes after p
           (vector-set! e e-n (string-trim (substring line 2)))
           (set! e-n (add1 e-n))]))))

  (values c p e))

(define (write-colfile str c p e outpath)
  (gvector-add! c additional-line)

  ;; .col is 1-indexed but log is 0-indexed
  (define seq (--> str
                   (string-split ", ")
                   seq-fix-0indexed->1indexed))
  
  (reorder! seq e)

  (call-with-output-file outpath
    (λ (out)
      (for ([l (in-gvector c)])
        (display "c " out)
        (displayln l out))
      (for ([l (in-gvector p)])
        (display "p " out)
        (displayln l out))
      (for ([l (in-vector e)])
        (display "e " out)
        (displayln l out)))
    #:exists 'replace))

;; seq is a list of vertices
;; e is a list of edges joined by space
(define (reorder! seq e)
  (define score-ht
    (for/hash ([(v i) (in-indexed (in-list seq))])
      (values v i)))
  (define n (length seq))

  (define (get s)
    (hash-ref score-ht s n))

  (define (min-index s)                 ; take edges in order of vertices
    (define i (string-find s " "))
    (min (get (substring s 0 i))
         (get (substring s (add1 i)))))

  (vector-sort! e < #:key min-index))

(define (pathwidth-log->solved?/seq path)
  (call-with-input-file path
    (λ (in)
      ;; file path
      (read-line in)

      (let loop ([seq? #f]
                 [last-seen #f])
        (define line (read-line in))
        (cond
          [(char<=? #\0 (string-ref line 0) #\9)
           (loop (not seq?)
                 (if seq?
                     line
                     last-seen))]
          [(and (regexp-match? #px"^.*\\.col\\W+\\d+\\W+\\d+\\W+\\d+\\W+\\d+$"
                               line)
                last-seen
                (not seq?))
           (values #t last-seen)]
          [else
           (values #f #f)])))))

(define (seq-fix-0indexed->1indexed l)
  (for/list ([x (in-list l)])
    (--> x
         string->number
         add1
         number->string)))
