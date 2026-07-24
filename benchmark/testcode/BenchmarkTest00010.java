package org.owasp.benchmark.testcode;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.sql.*;

@WebServlet(value="/sqli-00010")
public class BenchmarkTest00010 extends HttpServlet {

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

        String param = request.getParameter("search");
        if (param == null) param = "";

        String query = "SELECT * FROM products WHERE name LIKE ?";

        try {
            Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/benchmark", "root", "password");
            PreparedStatement pstmt = conn.prepareStatement(query);
            pstmt.setString(1, "%" + param + "%");
            ResultSet rs = pstmt.executeQuery();

            while (rs.next()) {
                response.getWriter().println(rs.getString("name"));
            }

            rs.close();
            pstmt.close();
            conn.close();
        } catch (SQLException e) {
            throw new ServletException(e);
        }
    }
}
