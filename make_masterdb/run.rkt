#lang racket

(require racket/exn)

(require "../util/macros.rkt")

;; path of markdown listing all results
(define input-index "../2023result/docs/solver/index.md")
(define output-csv "./master-db.csv")

(module+ main
  (printf "reading ~a~n" input-index)

  (call-with-output-file output-csv
    (λ (out)
      (write-csv-head out)
      
      (call-with-input-file input-index
        (λ (in)
          (let loop ()
            (unless (string=? (read-line in) "## Overall shortest (cpu)")
              (loop)))
          
          ;; skip until table body
          (for ([_ (in-range 3)]) (read-line in))

          (let loop ()
            (define line (read-line in))
            (unless (zero? (string-length line))
              (write-csv-line line out)
              (loop))))))
    #:exists 'replace)

  (printf "wrote to ~a~n" output-csv))

(define (write-csv-head out)
  (displayln "graph_name,vertices,edges,dat_file,tokens" out))

(define (write-csv-line line out)
  (match-define (regexp #rx"^\\|[^|]+?\\.dat \\[col\\]\\(([^|]+?\\.col)\\) \\[dat\\]\\(([^|]+?\\.dat)\\)|.*"
                        (list _ relative-col relative-dat))
    line)
  
  (define dat-path (relative->path relative-dat))
  (define col-path (relative->path relative-col))

  (define dat-name (relative->name relative-dat))
  (define col-name (relative->name relative-col))
  (define tokens (dat->num-token dat-path))
  (define-values (nodes edges)
    (col->nodes/edges col-path))

  (displayln (format "~a,~a,~a,~a,~a"
                     col-name
                     nodes
                     edges
                     dat-name
                     tokens)
             out))

(define (relative->path dat)
  (build-path (path-only input-index) dat))

(define (dat->num-token path)
  (call-with-input-file path
    (λ (in)
      (--> (read-line in)
           string-trim
           (string-count #\space)
           number->string))))

(define (col->nodes/edges path)
  ;; queen200x200 is gzipped
  (with-handlers ([exn:fail?
                   (λ (e)
                     (printf "couldn't find .col file for ~a: ~a~n" path (exn->string e))
                     (values "-1" "-1"))])
    (call-with-input-file path
      (λ (in)
        (define line
          (let loop ()
            (define line (read-line in))
            (if (string-prefix? line "p")
                line
                (loop))))
        (match-define (list _ nodes edges)
          (string-split line " "))
        (values (string-trim nodes)
                (string-trim edges))))))

;; remove .col or .dat from basename
(define (relative->name path)
  (--> path
       file-name-from-path
       (path-replace-extension "")
       path->string))

(define (string-count s x)
  (for/fold ([s 0])
            ([c (in-string s)]
             #:when (char=? x c))
    (add1 s)))
