package org.owasp.benchmark.testcode;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.sql.*;

@WebServlet(value="/sqli-00009")
public class BenchmarkTest00009 extends HttpServlet {

    private static final long serialVersionUID = 1L;

    @Override
    public void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doPost(request, response);
    }

    @Override
    public void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        response.setContentType("text/html;charset=UTF-8");

        String param = request.getParameter("id");

        String bar = doSomething(request, param);

        String sql = "DELETE FROM users WHERE id = ?";

        try {
            Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/benchmark", "root", "password");
            PreparedStatement pstmt = conn.prepareStatement(sql);
            pstmt.setInt(1, Integer.parseInt(bar));
            int rowsAffected = pstmt.executeUpdate();

            response.getWriter().println("Deleted " + rowsAffected + " rows");

            pstmt.close();
            conn.close();
        } catch (SQLException | NumberFormatException e) {
            throw new ServletException(e);
        }
    }

    private static String doSomething(HttpServletRequest request, String param) {
        return param;
    }
}
