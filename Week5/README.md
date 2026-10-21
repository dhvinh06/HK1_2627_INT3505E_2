1.  GET    /hotels                                  List hotel (filter city, star_min, amenity; cursor pagination)
2.  POST   /hotels                                  Tạo hotel
3.  GET    /hotels/{hotelId}                        Xem 1 hotel
4.  GET    /hotels/{hotelId}/room-types             List loại phòng của hotel
5.  POST   /hotels/{hotelId}/room-types             Tạo loại phòng
6.  POST   /guests                                  Tạo khách
7.  GET    /bookings                                List booking (filter guest_id, hotel_id, status)
8.  POST   /bookings                                Tạo booking (body có items)
9.  GET    /bookings/{bookingId}                    Xem 1 booking (kèm items)
10. PATCH  /bookings/{bookingId}                    Đổi trạng thái (huỷ, xác nhận)
11. POST   /bookings/{bookingId}/payments           Tạo thanh toán cho booking
12. POST   /hotels/{hotelId}/reviews                Viết review cho hotel     