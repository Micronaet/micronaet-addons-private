<html>
<head>
    <!--<style type="text/css">
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
    </style>-->
</head>
<body>
   <!--List of totalizer of the report:-->
   <% total_number = 0 %>
   
   <!--List of level of the report:-->
   <% level_partner = False %>
   <% level_type = False %>
   <% level_account = False %>
   <% level_user = False %>
   <% break_level = False %>
   
   <table>
   <!--Master loop:-->
   %for key, item in load_data(data):
       
       <% total_number += 1 %>
       <tr>
          <td>
           %if level_partner != item.intervent_partner_id.id:
               <% break_level = 'partner' %>
               <% level_partner = item.intervent_partner_id.id %>
               <% level_type = False %>
               <% level_account = False %>
               <% level_user = False %>
               ${item.intervent_partner_id.name|entity}
           %endif    
          </td>
          <td>
           %if level_type != key[1]:
               %if not break_level:               
                   <% break_level = 'type' %>
               %endif    
               <% level_type = key[1] %>
               <% level_account = False %>
               <% level_user = False %>
               ${key[1]|entity}
           %endif    
          </td>
          <td>
           %if level_account != item.account_id.id:
               %if not break_level:               
                   <% break_level = 'account' %>
               %endif    
               <% level_account = item.account_id.id %>
               <% level_user = False %>
               ${item.account_id.name|entity}
           %endif    
          <td>
          <td>
           %if level_user != item.user_id.id:
               %if not break_level:               
                   <% break_level = 'user' %>
               %endif    
               <% level_user = item.user_id.id %>
               ${item.user_id.name|entity}
           %endif    
          </td>
          <td>
               ${total_number|entity}
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
          
          <td>
               ${break_level|entity}
               <% break_level = False %>
          </td>          
       <tr>
   %endfor

   </table>
</body>
</html>
