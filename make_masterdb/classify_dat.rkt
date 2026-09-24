#lang racket

;; farthest variant (`ddreconf --longest`) ignores `t` in stfile
;; for farthest variant, consider only `s` to correctly count #unique instances

;; this program assigns unique ids to each `s` in dat_file (`dat_file_s_id`)

(define csv-file "./master-db.csv")     ; overwrite
(define graphs "../2023result/docs/solver/benchmark/")

(module+ main
  (printf "reading ~a~n" csv-file)
  (define out-s
    (call-with-input-file csv-file
      (λ (in)
        (call-with-output-string
         (λ (out)
           (patch in out))))))
  
  (display-to-file out-s csv-file #:exists 'replace)
  (printf "wrote to ~a~n" csv-file))

(define (patch in out)
  (define ht (make-hash))
  (define head (read-line in))
  (define i (index-of (string-split head ",") "dat_file"))
  (displayln (string-append head "," "dat_file_s_id") out)

  (define dats
    (find-files (λ (p) (path-has-extension? p #".dat")) graphs #:follow-links? #t))

  (for ([l (in-lines in)])
    (define dat-file (list-ref (string-split l ",") i))

    (match-define (list dat-file-path)
      (filter (λ (p)
                (string=? (path->string (file-name-from-path p))
                          (string-append dat-file ".dat")))
              dats))

    (define s-line
      (string-trim (call-with-input-file dat-file-path
                     (λ (in) (for/first ([l (in-lines in)]
                                         #:when (string-prefix? l "s "))
                               l)))))

    (define s-key (sort (string-split (substring s-line 2) " ") string<?))
    
    (define id (hash-ref! ht s-key (hash-count ht)))

    (displayln (string-append l "," (number->string id)) out)))

