analytics-0.1.0:
- bar chart for single company and signle rtype
- load data from rapi
- user can select company and rtype
- user can select time frame
- user can select timerange in case of pot records

analytics-0.2.0:
- table with financial data in accordance with selected schema
- bar chart for single company with multiple different records (new 
  record type are selected in table)
- user can remove selected records from bar chart
- user can switch view from rtype-time to time-rtype
- show empty columns and empty bars in chart
- fix labels on chart

- think about moving timeframe 'rtype' to financial statement type which is used
  by schemas also and create property inside recordtype with the same name and
  add this to FinancialStatementSchema
- remove deep dependeciens e.g. if self.rtype.timeframe == "pit":