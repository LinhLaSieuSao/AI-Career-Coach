# Synthetic CV parser fixtures

`create_cv_edge_cases()` writes temporary files for the automated parser tests:

- Vietnamese text PDF with a Unicode `ToUnicode` map
- two-column PDF with both column contents
- DOCX with a table and Vietnamese text
- image-only PDF for `SCANNED_PDF`
- zero-byte PDF/DOCX and a wrong-magic executable-like payload

All content is synthetic. Tests create these files under pytest's temporary directory, so no personal CV or generated binary is retained in the repository.
