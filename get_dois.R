library(rcrossref)
x <- cr_search(query='2072-4292', sort="year", type="Journal Article", rows=1000, year=2014)
writeLines(x$doi, con='MDPI_RS_2014_DOIs.csv')

