

    <!DOCTYPE html>
        
    <!-- Tables, from : http://www.tutorialrepublic.com/twitter-bootstrap-tutorial/bootstrap-tables.php-->
    <!-- sorting (todo) http://tutsme-webdesign.info/bootstrap-3-sortable-table/
    oder hübscher: http://drvic10k.github.io/bootstrap-sortable/
    -->

    <html>

    <head>

        <meta charset="utf-8">

        <title>Basic Bootstrap Template</title>

        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <!--link rel="stylesheet" type="text/css" href="css/bootstrap.min.css"-->
        <link href="http://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.0.0-rc2/css/bootstrap.css" rel="stylesheet" media="screen">

    </head>

    <body>



<table id="myTable" class="table">

        <thead>

            <tr>

                <th>Basename</th>
                <th>Category</th>
                <th>Prodname</th>
                <th>Vendor</th>

                <!--th>First Name</th-->

                <!--th>Last Name</th-->

                <!--th>Email</th-->

            </tr>

        </thead>

        <tbody>

           
  % for item in mydict:
  
    <tr>
        <td>{{item}}</td>
        <td>{{mydict[item]["category"]}}</td>
        <td>{{mydict[item]["prodname"]}}</td>
        <td>{{mydict[item]["vendor"]}}</td>
    </tr>
  % end

            
        </tbody>
    </table>


   <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
   <script type="text/javascript" src="js/jquery.tablesorter.min.js"></script>
    <script src="http://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>
    <!-- Include all compiled plugins (below), or include individual files as needed -->
    <script src="http://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.0.0-rc2/js/bootstrap.min.js"></script>
    <script src="js/jquery.tablesorter.min.js"></script>
        <script>
        $(document).ready(function(){
        $(function(){
        $("#myTable").tablesorter();
        });
        });
        </script>
    </body>

    </html>