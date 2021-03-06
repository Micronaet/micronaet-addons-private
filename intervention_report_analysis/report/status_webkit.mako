<html>
<head>
    <style type="text/css">
        ${css}

        /*Colori utilizzati:
          #b7bec8 blu celeste
          #f6cf3b giallo
          #7c7bad violetto
          #444242 grigio scuro
        */

        body {
            font-family: Arial, 'Times New Roman', Times, serif;
            font-size: 13px;
            }
        p {
            margin: 2px;
            }

        .partner {
            font-size: 13px;          
            font-weight: bold;  
            margin-top: 15px; 
            padding-left: 3px; 
            }
        .type_account {
            font-size: 11px;          
            font-weight: bold;  
            padding-left: 8px; 
            }
        .account {
            font-size: 9px;          
            padding-left: 13px; 
            }
        

        h2 {
            font-size: 13px;            
            }

        .red {
            background-color: #ffd5d5;
            /*A70010;*/
            font-weight: bold;
            }
        .blu {
            background-color: #d5e9ff;
            /*363AA7;*/
            font-weight: bold;
            }
        .green {
            background-color: #ade3b8;
            /*004E00;*/
            font-weight: bold;
            }
        .yellow {
            background-color: #fffccc;
            /*004E00;*/
            font-weight: bold;
            }
        
        .right {
            text-align:right;         
            }
        .center {
            text-align: center;
            }
        .left {
            text-align: left;
            }
        .even {
            background-color: #efeff8;
            }
        .odd {
            background-color: #FFFFFF;
            }
        
        .total {
            font-size: 11px;          
            font-weight: bold;  
            padding: 4px;
            background-color: #f6cf3b;
            }
        
        .center_line {
            text-align: center; 
            border: 1px solid #000; 
            padding: 3px;
            }

        table.list_table {
            border: 1px solid #000;             
            padding: 0px;
            margin: 0px;                        
            cellspacing: 0px;
            cellpadding: 0px;
            border-collapse: collapse;

            /*Non funziona il paginate*/
            -fs-table-paginate: paginate;
            }

        table.list_table tr, table.list_table tr td {
            page-break-inside: avoid;
            }        
        
        tr th{
            text-align: center;
            font-size: 10px;
            border: 1px solid #000; 
            background: #7c7bad;            
            color: #FFFFFF;            
            }
        thead {
            display: table-header-group;
            }
            
        tr td{
            text-align: center;
            font-size: 10px;
            border: 1px solid #000; 
            }
        .description{
            width: 250px;
            text-align: left;
            }
        .data{
            width: 50px;
            vertical-align: top;
            font-size: 8px;          
            font-weight: normal;
            /*color: #000000;*/
            }
        .nopb {
            page-break-inside: avoid;
            }
    </style>
</head>
<body>
   <!--List of totalizer of the report:-->
   <% 
   levels = ('partner', 'type', 'account', 'user')
   total = {
       'number': dict.fromkeys(levels, 0),
       'hour': dict.fromkeys(levels, 0),
       'hour_total': dict.fromkeys(levels, 0), # invoiced
       'internal': dict.fromkeys(levels, 0),
       'trip': dict.fromkeys(levels, 0),
       'free': dict.fromkeys(levels, 0),
       'todo': dict.fromkeys(levels, 0),
       'value': dict.fromkeys(levels, 0),          
       }
   old_data = dict.fromkeys(levels, False)
   header_data = dict.fromkeys(levels, False)
   %>
   
   <!--List of level of the report:-->
   <% 
   # Variables:
   i = 0
   break_level = False   
   float_format = '%2.2f'
   %>
   
   <!--Master loop:-->
   %for key, item in load_data(data):
       <!--Update counters:-->
       <%        
       i += 1
       break_level = False
       %>

       <!--First loop-->
       %if i == 1: # First line:
           <% 
           old_data['partner'] = item.intervent_partner_id.id
           old_data['type'] = key[1]
           old_data['account'] = item.account_id.id
           old_data['user'] = item.user_id.id
           
           # TODO Header elements for write table header elements:<<<<<<<<<<<<<
           header_data['partner'] = item.intervent_partner_id.name or '#ERR'
           header_data['type'] = key[1]
           header_data['account'] = item.account_id.name if item.account_id else '#ERR'
           #header['user'] = item.user_id.name
           %>
           ${table_start(header_data)}
           ${write_header()}   
       %endif
       
       <!--Break check:-->       
       %if old_data['partner'] != item.intervent_partner_id.id:
           <% 
           break_level = 'partner' 
           header_data['partner'] = item.intervent_partner_id.name or '#ERR'
           %>
       %else:
           %if old_data['type'] != key[1]:
               <% 
               break_level = 'type' 
               header_data['type'] = key[1]
               %>
           %else:
               %if old_data['account'] != item.account_id.id:
                   <% 
                   break_level = 'account' 
                   header_data['account'] = item.account_id.name if item.account_id else '#ERR'
                   %>
               %else:
                   %if old_data['user'] != item.user_id.id:
                       <% 
                       break_level = 'user' 
                       #header['user'] = item.user_id.name
                       %>
                   %endif
               %endif
           %endif
       %endif

       <!--Write total if break level:-->
       %if break_level and break_level in ('partner', 'type', 'account'):
           ${write_total(total, break_level, header_data, new_table=break_level == 'partner')}
       %endif

       <!--Update here total:-->
       <% 
       dict_operation(total['number'], 1, 'add') # number
       dict_operation(total['hour'], item.intervent_duration, 'add') # total net intevent
       dict_operation(total['hour_total'], item.intervent_total, 'add') # total invoiced
       dict_operation(total['trip'], item.trip_hour, 'add') # trip
       dict_operation(total['internal'], item.unit_amount, 'add') # internal
       %>

       <!--Partner level:-->
       %if break_level == 'partner':               
           <% 
           # Reset old value:
           old_data['partner'] = item.intervent_partner_id.id
           old_data['type'] = key[1]
           old_data['account'] = item.account_id.id
           old_data['user'] = item.user_id.id

           # Reset counters:
           dict_operation(total['number'], 1, 'set')
           dict_operation(total['hour'], item.intervent_duration, 'set')
           dict_operation(total['hour_total'], item.intervent_total, 'set')
           dict_operation(total['trip'], item.trip_hour, 'set')
           dict_operation(total['internal'], item.unit_amount, 'set')
           %>
       %endif  
       <!--
       WRITE IN TABLE CHANGE (when total detail are writed)
       %if i == 1 or break_level and break_level in ('partner'):
           <tr><td>${item.intervent_partner_id.name|entity}</td>
       %else:
           <tr><td>&nbsp;</td>                   
       %endif
       -->
      
       <!--Type level:-->
       %if break_level == 'type':
           <%
           # Reset old value
           old_data['type'] = key[1]
           old_data['account'] = item.account_id.id
           old_data['user'] = item.user_id.id

           # Reset counters:
           total['number']['type'] = 1
           total['number']['account'] = 1
           total['number']['user'] = 1
           
           total['hour']['type'] = item.intervent_duration
           total['hour']['account'] = item.intervent_duration
           total['hour']['user'] = item.intervent_duration

           total['hour_total']['type'] = item.intervent_total
           total['hour_total']['account'] = item.intervent_total
           total['hour_total']['user'] = item.intervent_total

           total['trip']['type'] = item.trip_hour
           total['trip']['account'] = item.trip_hour
           total['trip']['user'] = item.trip_hour

           total['internal']['type'] = item.unit_amount
           total['internal']['account'] = item.unit_amount
           total['internal']['user'] = item.unit_amount
           %>
       %endif
       %if i == 1 or break_level and break_level in ('partner', 'type'): 
           <td>${key[1]|entity}</td>
       %else:
           <td>&nbsp;</td>                   
       %endif    
      
       <!--Account level:-->
       %if break_level == 'account':
           <% 
           # Reset old value
           old_data['account'] = item.account_id.id
           old_data['user'] = item.user_id.id
 
           # Reset counters:
           total['number']['account'] = 1
           total['number']['user'] = 1

           total['hour']['account'] = item.intervent_duration
           total['hour']['user'] = item.intervent_duration

           total['hour_total']['account'] = item.intervent_total
           total['hour_total']['user'] = item.intervent_total

           total['trip']['account'] = item.trip_hour
           total['trip']['user'] = item.trip_hour

           total['internal']['account'] = item.unit_amount
           total['internal']['user'] = item.unit_amount
           %>
       %endif  
       %if i == 1 or break_level and break_level in ('partner', 'type', 'account'):
           <td>${item.account_id.name|entity}</td>
       %else:
           <td>&nbsp;</td>                   
       %endif    
      
       <!--User level:-->      
       %if break_level == 'user':
           <% 
           # Reset old value
           old_data['user'] = item.user_id.id

           # Reset counters:
           total['number']['user'] = 1 

           total['hour']['user'] = item.intervent_duration

           total['hour_total']['user'] = item.intervent_total

           total['trip']['user'] = item.trip_hour

           total['internal']['user'] = item.unit_amount
           %> 
       %endif
       %if i == 1 or break_level and break_level in ('partner', 'type', 'account', 'user'):
           <td>${item.user_id.name|entity}</td>
       %else:
           <td>&nbsp;</td>                   
       %endif    
      
      <!--Data elements:-->
      <td>
           ${item.date_start|entity}
      </td>      
          
      <td>
           ${float_format % item.intervent_duration|entity}
      </td>          
      
      <td>
           ${'(man.)' if item.manual_total else ''|entity}
           ${float_format % item.intervent_total|entity}
      </td>          
      
      <td>
           ${'(man.)' if item.manual_total_internal else ''|entity}
           ${float_format % item.unit_amount|entity}
      </td>          
      
      <td>
           ${float_format % item.trip_hour|entity}
      </td>
      
      <!-- Extra line for total ${break_level|entity}-->
      </tr>
   %endfor
   <!--TODO start!?!?!?-->
   %if not start:
       ${write_total(total, 'partner', None, new_table=False)}
   %endif    

   ${table_end()}
</body>
</html>
