;;; queequeg.el --- a simple interface of Queequeg.

;; Copyright (C) 2004 TSUCHIYA Masatoshi <tsuchiya@namazu.org>

;; Author: TSUCHIYA Masatoshi <tsuchiya@namazu.org>
;; Keywords: Grammar Checker
;; Version: $Revision: 1.8 $

;; This program is free software; you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation; either version 2, or (at your option)
;; any later version.

;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with this program; if not, you can either send email to this
;; program's maintainer or write to: The Free Software Foundation,
;; Inc.; 59 Temple Place, Suite 330; Boston, MA 02111-1307, USA.

;;; Commentary:

;; This is a simple interface of Queequeg.  For more detail about
;; Queequeg, see:
;;
;;     http://queequeg.sourceforge.net/

;; The latest version of this program can be downloaded from
;; http://namazu.org/~tsuchiya/elisp/queequeg.el.

;;; Install:

;; This program depends on shell-command.el, that can be downloaded
;; from http://namazu.org/~tsuchiya/elisp/shell-command.el.  Install
;; it into an appropriate directory before installing this program.

;; Install this file to an appropriate directory, and put these lines
;; into your ~/.emacs.

;;     (autoload 'qq "queequeg" nil t)

;;; Code:
(require 'ansi-color)
(require 'compile)
(require 'shell-command)

(defgroup queequeg nil
  "User variables for emacs queequeg interface."
  :group 'applications)

(defcustom queequeg-prompt
  "Grammar check [%w]%$ "
  "*Prompt string of `queequeg'."
  :type 'string
  :group 'queequeg)

(defcustom queequeg-command
  "qq"
  "*Name of the executable file of the Queequeg command."
  :type 'string
  :group 'queequeg)

(defcustom queequeg-options
  '((cond
     ((memq major-mode '(tex-mode latex-mode yatex-mode)) "-t")
     ((memq major-mode '(html-mode sgml-mode yahtml-mode)) "-l")
     (t "-p")))
  "*Options of the Queequeg command."
  :type '(repeat sexp)
  :group 'queequeg)

(defcustom queequeg-ignore-escape-sequence
  (eq 'light (cdr (assq 'background-mode (frame-parameters))))
  "*Non-nil means taht all escape sequences are ignored.
Because escape sequences printed by Queequeg are fitted to dark
backgrounds, you should set this option when you are using emacs in
light background."
  :type 'boolean
  :group 'queequeg)

(let (current-load-list)
  (defadvice compilation-filter
    (after queequeg-compilation-filter activate compile)
    "Translate ANSI escape sequences in the result of `queequeg'."
    (when (buffer-live-p (process-buffer (ad-get-arg 0)))
      (save-excursion
	(set-buffer (process-buffer (ad-get-arg 0)))
	(when (string-equal (nth 2 compilation-arguments) "queequeg")
	  (goto-char (process-mark (ad-get-arg 0)))
	  (forward-line 0)
	  (let ((beg (point-min-marker))
		(end (point-marker)))
	    (funcall (if queequeg-ignore-escape-sequence
			 'ansi-color-filter-region
		       'ansi-color-apply-on-region)
		     beg end)
	    (set-marker beg nil)
	    (set-marker end nil)))))))

(defun queequeg (command)
  "Run Queequeg, with user-specified args, and collect output in a buffer."
  (interactive
   (list
    (shell-command-read-minibuffer
     queequeg-prompt
     default-directory
     (mapconcat 'identity
		(nconc (list queequeg-command)
		       (mapcar 'eval queequeg-options)
		       (when (buffer-file-name)
			 (list (file-relative-name
				(buffer-file-name)
				default-directory))))
		" "))))
  (compile-internal command "No more errors" "queequeg"))

(defalias 'qq 'queequeg)

(provide 'queequeg)

;;; queequeg.el ends here