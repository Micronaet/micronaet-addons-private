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

        p {
           margin:2px;
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
            font-size:13px;            
        }

        .red {
            background-color:#ffd5d5;
            /*A70010;*/
            font-weight:bold;
        }
        .blu {
            background-color:#d5e9ff;
            /*363AA7;*/
            font-weight:bold;
        }
        .green {
            background-color:#ade3b8;
            /*004E00;*/
            font-weight:bold;
        }
        .yellow {
            background-color:#fffccc;
            /*004E00;*/
            font-weight:bold;
        }
        
        .right {
            text-align:right;         
        }
        .center {
            text-align:center;
        }
        .left {
            text-align:left;
        }
        .even {
            background-color: #efeff8;
        }
        .odd {
            background-color: #FFFFFF;
        }
        
        .total {
            font-size:11px;          
            font-weight:bold;  
            padding:4px;
            background-color: #f6cf3b;
        }
        
        .center_line {
            text-align:center; 
            border:1px solid #000; 
            padding:3px;
        }

        table.list_table {
            border:1px solid #000;             
            padding:0px;
            margin:0px;                        
            cellspacing:0px;
            cellpadding:0px;
            border-collapse:collapse;
            
            /*Non funziona il paginate*/
            -fs-table-paginate: paginate;
        }

        table.list_table tr, table.list_table tr td {
            page-break-inside:avoid;
        }        
        
        thead tr th{
            text-align:center;
            font-size:10px;
            border:1px solid #000; 
            background:#7c7bad;            
        }
        thead {
            display: table-header-group;
            }
            
        tbody tr td{
            text-align:center;
            font-size:10px;
            border:1px solid #000; 
        }
        .description{
              width:250px;
              text-align:left;
        }
        .data{
              width:50px;
              vertical-align:top;
              font-size:8px;          
              font-weight:normal;
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
   old_value = dict.fromkeys(levels, False)
   %>
   
   <!--List of level of the report:-->
   <% 
   # Variables:
   i = 0
   break_level = False   
   float_format = '%2.2f'
   %>
   
   ${table_start()}
   ${write_header()}   
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
           old_value['partner'] = item.intervent_partner_id.id
           old_value['type'] = key[1]
           old_value['account'] = item.account_id.id
           old_value['user'] = item.user_id.id
           %>
       %endif
       
       <!--Break check:-->       
       %if old_value['partner'] != item.intervent_partner_id.id:
           <% break_level = 'partner' %>
       %else:
           %if old_value['type'] != key[1]:
               <% break_level = 'type' %>
           %else:
               %if old_value['account'] != item.account_id.id:
                   <% break_level = 'account' %>
               %else:
                   %if old_value['user'] != item.user_id.id:
                       <% break_level = 'user' %>
                   %endif
               %endif
           %endif
       %endif

       <!--Write total if break level:-->
       %if break_level and  break_level in ('partner', 'type', 'account'):
           ${write_total(total, break_level, new_table=break_level == 'partner')}
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
           old_value['partner'] = item.intervent_partner_id.id
           old_value['type'] = key[1]
           old_value['account'] = item.account_id.id
           old_value['user'] = item.user_id.id

           # Reset counters:
           dict_operation(total['number'], 1, 'set')
           dict_operation(total['hour'], item.intervent_duration, 'set')
           dict_operation(total['hour_total'], item.intervent_total, 'set')
           dict_operation(total['trip'], item.trip_hour, 'set')
           dict_operation(total['internal'], item.unit_amount, 'set')
           %>
       %endif  
       %if i == 1 or break_level and break_level in ('partner'):
           <tr><td>${item.intervent_partner_id.name|entity}</td>
       %else:
           <tr><td>&nbsp;</td>                   
       %endif
      
       <!--Type level:-->
       %if break_level == 'type':
           <%
           # Reset old value
           old_value['type'] = key[1]
           old_value['account'] = item.account_id.id
           old_value['user'] = item.user_id.id

           # Reset counters:
           dict_operation(total['number'], 1, 'set', 
               ('type', 'account', 'user'))
           
           dict_operation(total['hour'], item.intervent_duration, 'set', 
               ('type', 'account', 'user'))

           dict_operation(total['hour_total'], item.intervent_total, 'set', 
               ('type', 'account', 'user'))

           dict_operation(total['trip'], item.trip_hour, 'set', 
               ('type', 'account', 'user'))

           dict_operation(total['internal'], item.unit_amount, 'set', 
               ('type', 'account', 'user'))
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
           old_value['account'] = item.account_id.id
           old_value['user'] = item.user_id.id
 
           # Reset counters:
           dict_operation(total['number'], 1, 'set', 
               ('account', 'user'))
           
           dict_operation(total['hour'], item.intervent_duration, 'set', 
               ('account', 'user'))

           dict_operation(total['hour_total'], item.intervent_total, 'set', 
               ('account', 'user'))

           dict_operation(total['trip'], item.trip_hour, 'set', 
               ('account', 'user'))

           dict_operation(total['internal'], item.unit_amount, 'set', 
               ('account', 'user'))
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
           old_value['user'] = item.user_id.id

           # Reset counters:
           dict_operation(total['number'], 1, 'set', 
               ('user'))
           
           dict_operation(total['hour'], item.intervent_duration, 'set', 
               ('user'))

           dict_operation(total['hour_total'], item.intervent_total, 'set', 
               ('user'))

           dict_operation(total['trip'], item.trip_hour, 'set', 
               ('user'))

           dict_operation(total['internal'], item.unit_amount, 'set', 
               ('user'))
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
   %if not start:
       ${write_total(total, 'partner', new_table=False)}
   %endif    

   ${table_end()}
</body>
</html>
