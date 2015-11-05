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
   elements = ('row', 'partner', 'type', 'account', 'user')
   total = {
       'number': dict.fromkeys(elements, 0),
       'hour': dict.fromkeys(elements, 0),
       'free': dict.fromkeys(elements, 0),
       'todo': dict.fromkeys(elements, 0),
       'value': dict.fromkeys(elements, 0),          
       }
   %>
   
   <!--List of level of the report:-->
   <% 
   start = True
   
   level_partner = False
   level_type = False
   level_account = False
   level_user = False
   break_level = False 
   %>
   
   ${table_start()}
   ${write_header()}
   
   <!--Master loop:-->
   %for key, item in load_data(data):       
       <% dict_operation(total['number'], 1, 'add') %>
   
          <!--Partner level:-->
           %if level_partner != item.intervent_partner_id.id:
               <% 
               # Break level setup:
               break_level = 'partner'
               %>

               %if start: # no total if is the fist line:
                   <% 
                   start = False 
                   %>
               %else:
                   ${write_total(total, break_level, new_table=True)}
               %endif
                   
               <% 
               # Reset old value:
               level_partner = item.intervent_partner_id.id
               level_type = False
               level_account = False
               level_user = False 

               # Reset counters:
               total['number']['partner'] = 1
               total['number']['type'] = 1
               total['number']['account'] = 1
               total['number']['user'] = 1
               %>
               <tr><td>
                      ${item.intervent_partner_id.name|entity}
                   </td>
           %else:
               <tr><td>&nbsp;</td>                   
           %endif    
          
          <!--Type level:-->
           %if level_type != key[1]:
               <% 
               # Break level setup:
               %>
               
               %if not break_level:               
                   <% break_level = 'type' %>
                   <!--${write_total(total, break_level, new_table=False)}-->
               %endif    

               <%
               # Reset old value
               level_type = key[1]
               level_account = False
               level_user = False

               # Reset counters:
               total['number']['type'] = 1
               total['number']['account'] = 1
               total['number']['user'] = 1
               %> 

               <td>
                   ${key[1][:3]|entity}
               </td>
           %else:
               <td>&nbsp;</td>                   
           %endif    
          
          <!--Account level:-->
          <td>
           %if level_account != item.account_id.id:
               %if not break_level:               
                   <% break_level = 'account' %>
               %endif    

               <% 
               # Break level setup:
               level_account = item.account_id.id
               level_user = False 

               # Reset counters:
               total['number']['account'] = 1
               total['number']['user'] = 1
               %> 

               ${item.account_id.name|entity}
           %endif    
          </td>
          
          <!--User level:-->
          <td>
           %if level_user != item.user_id.id:
               %if not break_level:               
                   <% break_level = 'user' %>
               %endif    

               <% 
               # Break level setup:
               level_user = item.user_id.id

               # Reset counters:
               total['number']['user'] = 1 
               %> 

               ${item.user_id.name|entity}
           %endif    
          </td>
          
          <!--Data elements:-->
          <td>
               ${item.date_start|entity}
          </td>      
              
          <td>
               ${item.intervent_duration|entity}
          </td>          
          
          <td>
               ${item.manual_total|entity}               
               ${item.intervent_total|entity}
          </td>          
          
          <td>
               ${item.manual_total_internal|entity}
               ${item.unit_amount|entity}
          </td>          
          
          <td>
               ${item.trip_hour|entity}
          </td>
          
          <!-- Extra line for total-->
          <td></td><td></td><td></td><td></td><td></td></tr>

           %if break_level:                   
               <% break_level = False %>
           %endif
   %endfor
   %if not start:
       ${write_total(total, 'partner', new_table=False)}
   %endif    

   ${table_end()}
</body>
</html>
