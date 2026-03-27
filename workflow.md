1. fetch the url and get the paper: parse the main text of the paper and write to a context.md file in a local .cache

2. list the data available in the supplementaries/data availability sections.if no explicit sections, infer a possible location from the main text. 

   a. from the list,  confirm which dataset(s)  the user wants to fetch. 

3. For element in the list:  if the target datasets come from OTHER publications  go back to 1.

   a. get the LINK (url/publication/excel/csv/gtihub) that it is linked to (soemtimes this will be inside the supplements of a DIFFERENT publication)
   b. scan the contents of the 
