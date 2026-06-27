#lang racket

;; parse stats lines of /usr/bin/time -v

(require racket/cmdline)

(require "../util/macros.rkt")

(define indir (make-parameter "../run_pathwidth_opt/output_1h/"))
(define out-csv (make-parameter "out.csv"))

(module+ main
  (command-line
   #:once-each
   ["--indir" path
              "where to find log files from Pathwidth"
              (indir path)]
   ["--out" path
            "output csv file"
            (out-csv path)]
   #:args ()
   (void))

  (call-with-output-file (out-csv)
    (λ (out)
      (displayln "graph_name,exit_status,cpu_time,wallclock_time,maximum_resident_set_size" out)
      (for ([p (in-directory (indir))]
            #:when (path-has-extension? p #".log"))
        (printf "read ~a~n" p)
        
        (define-values (graph verbose)
          (call-with-input-file p parse))
        (match-define (verbose-time
                       exit-status
                       cpu-time
                       wallclock-time
                       maximum-resident-set-size)
          verbose)

        (fprintf out
                 "~a,~a,~a,~a,~a~n"
                 graph
                 exit-status
                 cpu-time
                 wallclock-time
                 maximum-resident-set-size)))
    #:exists 'replace)

  (displayln "done"))

(struct verbose-time (exit-status
                      cpu-time          ; usr + sys
                      wallclock-time
                      maximum-resident-set-size)
  #:mutable)

(define (parse in)
  (define graph #f)
  (define this-verbose-time (verbose-time #f #f #f #f))

  (for/first ([line (in-lines in)]
              #:when (string-prefix? line "\tCommand being timed: "))
    (set! graph
          (match line
            [(regexp #rx".*/([^/]+?)\\.col"
                     (list _ col))
             col])))

  (define usr
    (--> (read-line in)
         (substring (string-length "\tUser time (seconds): "))
         string->number))

  (define sys
    (--> (read-line in)
         (substring (string-length "\tSystem time (seconds): "))
         string->number))

  (set-verbose-time-cpu-time!
   this-verbose-time
   (--> (+ usr sys)
        number->string))

  (read-line in)                        ; Percent of CPU

  (set-verbose-time-wallclock-time!
   this-verbose-time
   (as-> (read-line in) $
         (substring $ (string-length "\tElapsed (wall clock) time (h:mm:ss or m:ss): "))
         (match $
           [(pregexp "^(\\d+):(\\d\\d):(\\d\\d)$"
                     (list _ (app string->number h) (app string->number m) (app string->number s)))
            (+ (* 60 60 h) (* 60 m) s)]
           [(pregexp "^(\\d+):(\\d\\d(?:.\\d\\d)?)$"
                     (list _ (app string->number m) (app string->number s)))
            (+ (* 60 m) s)])))

  (read-line in)                        ; Average shared
  (read-line in)                        ; Average unshared
  (read-line in)                        ; Average stack
  (read-line in)                        ; Average total

  (set-verbose-time-maximum-resident-set-size!
   this-verbose-time
   (--> (read-line in)
        (substring (string-length "\tMaximum resident set size (kbytes): "))))

  (read-line in)                        ; Average resident
  (read-line in)                        ; Major page faults
  (read-line in)                        ; Minor page faults
  (read-line in)                        ; Voluntary context
  (read-line in)                        ; Involuntary
  (read-line in)                        ; Swaps
  (read-line in)                        ; File inputs
  (read-line in)                        ; File outputs
  (read-line in)                        ; Socket messages
  (read-line in)                        ; Socket received
  (read-line in)                        ; Signals
  (read-line in)                        ; Page size

  (set-verbose-time-exit-status!
   this-verbose-time
   (--> (read-line in)
        (substring (string-length "\tExit status: "))))

  (values graph this-verbose-time))
