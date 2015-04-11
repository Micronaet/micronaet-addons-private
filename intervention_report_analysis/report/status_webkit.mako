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
   <% old_partner = False %>
   <% opened_header = False %>
   <% row_pending = False %>
   
   %for order, item in load_data(data):
       <% need_header = False %>           
       
       <!--Check break partner code:-->
       %if old_partner != item.intervent_partner_id.id:
           <% need_header = True %>           
           <% old_partner = item.intervent_partner_id.id %>
           <% old_type = False %>
           <% old_account = False %>
           <% old_user = False %>
           <p class='partner'>
               ${item.intervent_partner_id.name|entity}
           </p>
       %endif

       <!-- Check break Contract / Generic account-->
       %if old_type != order[1]:
           <% need_header = True %>           
           <% old_type = order[1] %>
           <% old_account = False %>
           <% old_user = False %>
           <p class='type_account'>
               ${order[1]|entity}
           </p>
       %endif

       <!-- Check break analytic account-->
       %if order[1] == 'Contratti' and old_account != item.account_id.id:
           <% need_header = True %>           
           <% old_account = item.account_id.id %>
           <% old_user = False %>
           <p class='account'>
               ${item.account_id.name|entity}
           </p>
       %endif

       %if need_header: 
           %if opened_header:
               </table>
           %endif    
           <% opened_header = True %>
           <table class="list_table">      
               <thead>
                   <tr>
                       <th class='description'>Utente</th>
                       <th class='description'>#</th>
                       <th class='description'></th>
                       <th class='description'></th>
                   </tr>
               </thead>                   
       %endif                      
       
       %if old_user == item.user_id.name:
           <!--Increment totals-->
           <% total_number += 1 %>
           <% row_pending = True %>
           
       %else:
           <!--First element:-->
           %if not old_user:
               <% old_user = item.user_id.name %>
               <% total_number = 1 %>
           %else:
               
               <!-- Write row with totals:-->           
               <tr>
                   <td class='description'>${item.user_id.name|entity}</td>
                   <td class='description'>${total_number|entity}</td>
                   <td class='description'></td>
                   <td class='description'></td>
               </tr>    
               <!-- reset counters:-->
               <% old_user = item.user_id.name %>
               <% total_number = 0 %>
               <% row_pending = False %>
           %endif    
       %endif    

   %endfor
   %if row_pending:
       <tr>
           <td class='description'>${item.user_id.name|entity}</td>
           <td class='description'></td>
           <td class='description'></td>
           <td class='description'></td>
       </tr>    
   %endif    

   <!--Last close-->
   %if opened_header:
       </table>
   %endif    
</body>
</html>
