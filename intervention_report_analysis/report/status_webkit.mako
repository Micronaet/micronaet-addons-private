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
   <% setLang('it_IT') %>

   <% old_partner = False %>
   
   %for orer, item in load_data(data):
       <!--Check break partner code:-->
       %if not old_partner or old_partner != item.intervent_partner_id.id:
           %if old_partner:
               </table>
           %endif    
           

           <% old_partner = item.intervent_partner_id.id %>
           <% old_account = item.account_id.id %>
           <% old_user = item.user_id.id %>
           
           <p>
           ${item.intervent_partner_id.name|entity}
           </p>               

           <table class="list_table">      
               <!-- ################## HEADER ################################### -->
               <thead>
                   <tr>
                       <th class='description'>Conto analtico</th>
                       <th class='description'>Utente</th>
                       <th class='description'></th>
                       <th class='description'></th>
                       <th class='description'></th>
                   </tr>
               </thead>
       %endif
           <!-- ################## BODY ##################################### -->
           <tbody>
               <tr>
                   <td class='description'><% item.acount_id.name|entity%></td>
                   <td class='description'></td>
                   <td class='description'></td>
                   <td class='description'></td>
                   <td class='description'></td>
               </tr>    
           </tbody>
   %endfor
</body>
</html>
